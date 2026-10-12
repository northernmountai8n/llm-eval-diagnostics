"""Small OpenCompass run on the pinned Qwen2.5-1.5B base model.

The built-in CEval config points to opencompass/ceval-exam, which is not
available from this host. Keep its 5-shot PPL protocol, but use a local CSV
export of ceval/ceval-exam and select only computer_network (19 val rows).
"""

from opencompass.datasets import CEvalDataset
from opencompass.models import HuggingFaceBaseModel
from opencompass.openicl.icl_evaluator import AccEvaluator
from opencompass.openicl.icl_inferencer import PPLInferencer
from opencompass.openicl.icl_prompt_template import PromptTemplate
from opencompass.openicl.icl_retriever import FixKRetriever


REVISION = '8faed761d45a263340a0528343f099c05c9a4323'

datasets = [
    dict(
        type=CEvalDataset,
        path='data/day19_ceval_opencompass',
        name='computer_network',
        local_mode=True,
        abbr='ceval-computer_network',
        reader_cfg=dict(
            input_columns=['question', 'A', 'B', 'C', 'D'],
            output_column='answer',
            train_split='dev',
            test_split='val',
        ),
        infer_cfg=dict(
            ice_template=dict(
                type=PromptTemplate,
                template={
                    answer: dict(
                        begin='</E>',
                        round=[
                            dict(
                                role='HUMAN',
                                prompt='以下是中国关于计算机网络考试的单项选择题，请选出其中的正确答案。\n'
                                '{question}\nA. {A}\nB. {B}\nC. {C}\nD. {D}\n答案: ',
                            ),
                            dict(role='BOT', prompt=answer),
                        ],
                    )
                    for answer in ['A', 'B', 'C', 'D']
                },
                ice_token='</E>',
            ),
            retriever=dict(type=FixKRetriever, fix_id_list=[0, 1, 2, 3, 4]),
            inferencer=dict(type=PPLInferencer),
        ),
        eval_cfg=dict(evaluator=dict(type=AccEvaluator)),
    )
]

models = [
    dict(
        type=HuggingFaceBaseModel,
        abbr='qwen2.5-1.5b-base-pinned',
        path='Qwen/Qwen2.5-1.5B',
        tokenizer_kwargs=dict(revision=REVISION),
        model_kwargs=dict(
            revision=REVISION,
            torch_dtype='bfloat16',
            device_map='cuda:0',
        ),
        max_seq_len=2048,
        max_out_len=16,
        batch_size=1,
        run_cfg=dict(num_gpus=1),
    )
]
