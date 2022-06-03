import pytest

from daft.dataclasses import dataclass
from daft.datarepo.log import DaftLakeLog
from daft.datarepo.query import (
    QueryColumn,
    _FilterPredicate,
    _GetDatarepoStage,
    _LimitStage,
    _FilterStage,
    _ApplyStage,
)
from daft.datarepo.datarepo import DataRepo

FAKE_DATAREPO_ID = "mydatarepo"
FAKE_DATAREPO_PATH = f"file:///tmp/fake_{FAKE_DATAREPO_ID}_path"


@dataclass
class MyFakeDataclass:
    foo: str


@pytest.fixture(scope="function")
def fake_datarepo() -> DataRepo:
    # TODO(jaychia): Use Datarepo client here instead once API stabilizes
    daft_lake_log = DaftLakeLog(FAKE_DATAREPO_PATH)
    return DataRepo(daft_lake_log)


def test_query_select_star(fake_datarepo: DataRepo) -> None:
    q = fake_datarepo.query(MyFakeDataclass)
    stages = [_GetDatarepoStage(daft_lake_log=fake_datarepo._log, dtype=MyFakeDataclass)]
    assert len(q._query_tree.nodes()) == 1
    assert [k for k in q._query_tree.nodes()][0] == q._root
    assert [v["stage"] for _, v in q._query_tree.nodes().items()] == stages


def test_query_limit(fake_datarepo: DataRepo) -> None:
    limit = 10
    q = fake_datarepo.query(MyFakeDataclass).limit(limit)
    stages = [_GetDatarepoStage(daft_lake_log=fake_datarepo._log, dtype=MyFakeDataclass), _LimitStage(limit=limit)]
    assert len(q._query_tree.nodes()) == 2
    assert [k for k in q._query_tree.nodes()][-1] == q._root
    assert [v["stage"] for _, v in q._query_tree.nodes().items()] == stages


def test_query_filter(fake_datarepo: DataRepo) -> None:
    pred = _FilterPredicate(left="id", comparator=">", right="5")
    q = fake_datarepo.query(MyFakeDataclass).filter(pred)
    stages = [_GetDatarepoStage(daft_lake_log=fake_datarepo._log, dtype=MyFakeDataclass), _FilterStage(predicate=pred)]
    assert len(q._query_tree.nodes()) == 2
    assert [k for k in q._query_tree.nodes()][-1] == q._root
    assert [v["stage"] for _, v in q._query_tree.nodes().items()] == stages


def test_query_apply(fake_datarepo: DataRepo) -> None:
    f = lambda x: 1
    q = fake_datarepo.query(MyFakeDataclass).apply(f, QueryColumn(name="foo"), somekwarg=QueryColumn(name="bar"))
    stages = [
        _GetDatarepoStage(daft_lake_log=fake_datarepo._log, dtype=MyFakeDataclass),
        _ApplyStage(f=f, args=(QueryColumn(name="foo"),), kwargs={"somekwarg": QueryColumn(name="bar")}),
    ]
    assert len(q._query_tree.nodes()) == 2
    assert [k for k in q._query_tree.nodes()][-1] == q._root
    assert [v["stage"] for _, v in q._query_tree.nodes().items()] == stages