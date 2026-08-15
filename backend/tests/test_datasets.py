from sqlalchemy.orm import Session

from app.eval.datasets import add_case, create_dataset, get_dataset, list_cases, list_datasets


def test_dataset_crud(db: Session):
    ds = create_dataset(db, name="电商", description="电商口径")
    assert get_dataset(db, ds.id).name == "电商"
    case = add_case(
        db, ds.id,
        input_prompt="退款率怎么算?",
        expected_behavior="返回退款口径",
        checks=[{"type": "contains", "value": "退款"}],
    )
    assert case.source_trace_id is None
    assert len(list_cases(db, ds.id)) == 1
    assert len(list_datasets(db)) == 1