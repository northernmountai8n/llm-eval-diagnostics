"""Day 18: concurrent API requests with retries and resumable results."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx


DEFAULT_URL = "http://127.0.0.1:8765/v1/chat/completions"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sample:
    id: int
    question: str
    gold: str | None = None


def load_samples(path: Path | None, count: int | None) -> list[Sample]:
    if path is None:
        return [Sample(i, f"第 {i} 道题") for i in range(1, (count or 4) + 1)]

    samples: list[Sample] = []
    seen: set[int] = set()
    with path.open("r", encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                sample_id = row["id"]
                question = row["question"]
                gold = row.get("gold")
                if not isinstance(sample_id, int) or isinstance(sample_id, bool):
                    raise ValueError("id must be an integer")
                if sample_id in seen:
                    raise ValueError(f"duplicate id {sample_id}")
                if not isinstance(question, str) or not question.strip():
                    raise ValueError("question must be nonempty text")
                if gold is not None and not isinstance(gold, str):
                    raise ValueError("gold must be text when present")
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number} is not a valid sample: {exc}") from exc
            samples.append(Sample(sample_id, question, gold))
            seen.add(sample_id)
            if count is not None and len(samples) >= count:
                break
    if not samples:
        raise ValueError(f"{path} contains no samples")
    return samples


def completed_rows(path: Path) -> dict[int, dict]:
    if not path.exists():
        return {}
    rows: dict[int, dict] = {}
    with path.open("r", encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                question_id = row["id"]
                if not isinstance(question_id, int) or isinstance(question_id, bool):
                    raise ValueError("id must be an integer")
                if not isinstance(row.get("question"), str) or not isinstance(row.get("answer"), str):
                    raise ValueError("question and answer must be text")
                if question_id in rows:
                    raise ValueError(f"duplicate id {question_id}")
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number} is not a valid result: {exc}") from exc
            rows[question_id] = row
    return rows


def save_row(sink, row: dict) -> None:
    sink.write(json.dumps(row, ensure_ascii=False) + "\n")
    sink.flush()
    os.fsync(sink.fileno())


async def ask(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    sample: Sample,
    url: str,
    model: str,
    request_options: dict,
    max_retries: int,
    backoff: float,
    demo_fail_once: bool,
    demo_fail_always: bool,
    run_id: str,
) -> tuple[int, str, dict]:
    question = sample.question
    if demo_fail_always and sample.id == 2:
        question = f"FAIL_ALWAYS:{run_id}:{question}"
    elif demo_fail_once and sample.id == 2:
        question = f"FAIL_ONCE:{run_id}:{question}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
    }
    payload.update(request_options)
    for attempt in range(max_retries + 1):
        try:
            async with semaphore:
                response = await client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
            choice = body["choices"][0]
            answer = choice["message"]["content"]
            if not isinstance(answer, str):
                raise ValueError("API response content is not text")
            metadata = {
                "response_model": body.get("model"),
                "system_fingerprint": body.get("system_fingerprint"),
                "finish_reason": choice.get("finish_reason"),
                "usage": body.get("usage"),
            }
            return sample.id, answer, metadata
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code
                if status != 429 and status < 500:
                    raise  # Bad requests should be fixed, not retried.
            if attempt == max_retries:
                raise
            delay = backoff * (2**attempt)
            logger.warning(
                "event=retry id=%d attempt=%d reason=%s delay_seconds=%.2f",
                sample.id,
                attempt + 1,
                type(exc).__name__,
                delay,
            )
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")


async def evaluate_one(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    sample: Sample,
    url: str,
    model: str,
    request_options: dict,
    max_retries: int,
    backoff: float,
    demo_fail_once: bool,
    demo_fail_always: bool,
    run_id: str,
) -> tuple[int, str | None, dict | None, Exception | None]:
    try:
        _, answer, metadata = await ask(
            client,
            semaphore,
            sample,
            url,
            model,
            request_options,
            max_retries,
            backoff,
            demo_fail_once,
            demo_fail_always,
            run_id,
        )
        return sample.id, answer, metadata, None
    except Exception as exc:
        return sample.id, None, None, exc


async def run(
    samples: list[Sample],
    concurrency: int,
    url: str,
    model: str,
    request_options: dict,
    api_key: str | None,
    timeout: float,
    max_retries: int,
    backoff: float,
    demo_fail_once: bool,
    demo_fail_always: bool,
    out: Path | None,
    failed_out: Path | None,
) -> int:
    if out is not None and failed_out is None:
        failed_out = out.with_suffix(".failed.jsonl")
    if out is not None and failed_out is not None and out.resolve() == failed_out.resolve():
        raise ValueError("success and failure paths must be different")
    semaphore = asyncio.Semaphore(concurrency)
    done = completed_rows(out) if out is not None else {}
    for sample in samples:
        if sample.id not in done:
            continue
        old = done[sample.id]
        if (
            old["question"] != sample.question
            or old.get("gold") != sample.gold
            or old.get("model", "day18-mock") != model
            or old.get("url", DEFAULT_URL) != url
            or old.get("request_options", {}) != request_options
        ):
            raise ValueError(f"result file contains id {sample.id} from a different input or model")
    pending = [sample for sample in samples if sample.id not in done]
    logger.info(
        "event=batch_start completed=%d pending=%d",
        len(samples) - len(pending),
        len(pending),
    )
    if not pending:
        return 0
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
    if failed_out is not None:
        failed_out.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    run_id = uuid.uuid4().hex
    sink = out.open("a", encoding="utf-8") if out is not None else None
    failed_sink = failed_out.open("a", encoding="utf-8") if failed_out is not None else None
    results: list[tuple[int, str]] = []
    failed: list[int] = []
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key is not None else None
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            requests = [
                evaluate_one(
                    client,
                    semaphore,
                    sample,
                    url,
                    model,
                    request_options,
                    max_retries,
                    backoff,
                    demo_fail_once,
                    demo_fail_always,
                    run_id,
                )
                for sample in pending
            ]
            sample_by_id = {sample.id: sample for sample in pending}
            for finished in asyncio.as_completed(requests):
                question_id, answer, metadata, error = await finished
                sample = sample_by_id[question_id]
                if error is not None:
                    failed.append(question_id)
                    status = error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
                    if failed_sink is not None:
                        save_row(
                            failed_sink,
                            {
                                "id": question_id,
                                "question": sample.question,
                                "gold": sample.gold,
                                "model": model,
                                "url": url,
                                "request_options": request_options,
                                "error_type": type(error).__name__,
                                "status_code": status,
                                "error": str(error),
                            },
                        )
                    logger.error(
                        "event=sample_failed id=%d error_type=%s status=%s",
                        question_id,
                        type(error).__name__,
                        status,
                    )
                    continue
                assert answer is not None
                results.append((question_id, answer))
                if sink is not None:
                    row = {
                        "id": question_id,
                        "question": sample.question,
                        "answer": answer,
                        "model": model,
                        "url": url,
                        "request_options": request_options,
                    }
                    if metadata is not None:
                        row.update(metadata)
                    if sample.gold is not None:
                        row["gold"] = sample.gold
                        row["exact_match"] = int(answer.strip() == sample.gold.strip())
                    save_row(
                        sink,
                        row,
                    )
                logger.info("event=sample_success id=%d", question_id)
    finally:
        if sink is not None:
            sink.close()
        if failed_sink is not None:
            failed_sink.close()
    elapsed = time.perf_counter() - started

    logger.info(
        "event=batch_done success=%d failed=%d concurrency=%d",
        len(results),
        len(failed),
        concurrency,
    )
    logger.info("event=throughput seconds=%.2f per_second=%.2f", elapsed, len(results) / elapsed)
    answer_by_id = {question_id: row["answer"] for question_id, row in done.items()}
    answer_by_id.update(results)
    with_gold = [sample for sample in samples if sample.gold is not None]
    if with_gold:
        scored = [sample for sample in with_gold if sample.id in answer_by_id]
        if len(scored) == len(with_gold):
            correct = sum(
                answer_by_id[sample.id].strip() == sample.gold.strip() for sample in scored
            )
            logger.info(
                "event=metric name=exact_match correct=%d total=%d value=%.4f",
                correct,
                len(scored),
                correct / len(scored),
            )
        else:
            logger.warning(
                "event=metric_incomplete scored=%d expected=%d",
                len(scored),
                len(with_gold),
            )
    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Resumable evaluation against a chat-completions API")
    parser.add_argument("--input", type=Path, help="JSONL with integer id, question, and optional gold")
    parser.add_argument("--count", type=int, help="Use first N input rows; demo defaults to four")
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default="day18-mock")
    parser.add_argument("--api-key-env", help="Name of an environment variable containing the API key")
    parser.add_argument("--thinking", choices=["enabled", "disabled"], help="DeepSeek thinking mode")
    parser.add_argument("--max-tokens", type=int, help="Maximum generated tokens")
    parser.add_argument("--temperature", type=float, help="Sampling temperature")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--backoff", type=float, default=0.25)
    demo_group = parser.add_mutually_exclusive_group()
    demo_group.add_argument("--demo-fail-once", action="store_true")
    demo_group.add_argument("--demo-fail-always", action="store_true")
    parser.add_argument("--out", type=Path, help="Append successful results to this JSONL file")
    parser.add_argument("--failed-out", type=Path, help="Append failed attempts to this JSONL file")
    args = parser.parse_args()
    if (args.count is not None and args.count < 1) or args.concurrency < 1:
        parser.error("--count and --concurrency must be positive")
    if args.timeout <= 0 or args.max_retries < 0 or args.backoff < 0:
        parser.error("--timeout must be positive; --max-retries and --backoff cannot be negative")
    if not args.model.strip():
        parser.error("--model cannot be empty")
    if args.max_tokens is not None and args.max_tokens < 1:
        parser.error("--max-tokens must be positive")
    if args.temperature is not None and not 0 <= args.temperature <= 2:
        parser.error("--temperature must be between 0 and 2")
    request_options = {}
    if args.thinking is not None:
        request_options["thinking"] = {"type": args.thinking}
    if args.max_tokens is not None:
        request_options["max_tokens"] = args.max_tokens
    if args.temperature is not None:
        request_options["temperature"] = args.temperature
    api_key = None
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            parser.error(f"environment variable {args.api_key_env} is not set")
    samples = load_samples(args.input, args.count)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stdout)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    exit_code = asyncio.run(
        run(
            samples,
            args.concurrency,
            args.url,
            args.model,
            request_options,
            api_key,
            args.timeout,
            args.max_retries,
            args.backoff,
            args.demo_fail_once,
            args.demo_fail_always,
            args.out,
            args.failed_out,
        )
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
