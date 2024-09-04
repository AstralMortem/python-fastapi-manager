import pytest
from unittest.mock import Mock, patch
from tortoise.models import ConfigurationError, Field, Manager, Query, Table
from fastapi_manager.utils.string import convert_to_snake_case
from fastapi_manager.db.models.meta import ModelMeta, MetaInfo

# Assuming MetaInfo and ModelMeta are imported from the module where they are defined


@pytest.fixture
def meta_mock():
    meta = Mock()
    meta.abstract = False
    meta.manager = Manager()
    meta.table = "test_table"
    meta.schema = None
    meta.app = "test_app"
    meta.app_label = None
    meta.model_name = None
    meta.pk_attr = "id"
    meta.table_description = ""
    return meta


@pytest.fixture
def field_mock():
    field = Mock(spec=Field)
    field.model_field_name = "test_field"
    field.source_field = "test_field_source"
    field.has_db_field = True
    field.generated = False
    return field


def test_meta_info_initialization(meta_mock):
    meta_info = MetaInfo(meta=meta_mock)

    assert meta_info.abstract == meta_mock.abstract
    assert meta_info.manager == meta_mock.manager
    assert meta_info.db_table == meta_mock.table
    assert meta_info.schema == meta_mock.schema
    assert meta_info.app == meta_mock.app


def test_meta_info_add_field(meta_mock, field_mock):
    meta_info = MetaInfo(meta=meta_mock)
    meta_info._model = Mock()

    meta_info.add_field("test_field", field_mock)

    assert "test_field" in meta_info.fields_map
    assert meta_info.fields_map["test_field"] == field_mock
    assert "test_field" in meta_info.fields_db_projection


def test_meta_info_add_duplicate_field(meta_mock, field_mock):
    meta_info = MetaInfo(meta=meta_mock)
    meta_info._model = Mock()

    meta_info.add_field("test_field", field_mock)

    with pytest.raises(ConfigurationError):
        meta_info.add_field("test_field", field_mock)


def test_meta_info_db_property(meta_mock):
    meta_info = MetaInfo(meta=meta_mock)
    meta_info._model = Mock()

    with pytest.raises(ConfigurationError):
        _ = meta_info.db

    meta_info.default_connection = "default"
    with patch("tortoise.models.connections.get") as mock_get:
        db_client = meta_info.db
        mock_get.assert_called_once_with("default")


def test_model_meta_new_class():
    meta_mock = Mock()
    meta_mock.app_label = "test_app"
    meta_mock.model_name = "test_model"
    meta_mock.apps = Mock()

    class BaseModel:
        pass

    attrs = {
        "__module__": "test_module",
        "_meta": meta_mock,
    }

    new_class = ModelMeta("TestModel", (BaseModel,), attrs)

    assert new_class._meta.app == "test_app"
    assert new_class._meta.model_name == "test_model"
    assert new_class._meta.apps is not None

    # Test that the model name is converted to snake case if not explicitly set
    new_class._meta.model_name = None
    snake_case_name = convert_to_snake_case("TestModel")
    assert new_class._meta.model_name == snake_case_name


def test_model_meta_without_app_label():
    with pytest.raises(RuntimeError):

        class TestModel(metaclass=ModelMeta):
            class Meta:
                abstract = False
                app_label = None
                app = None

            __module__ = "test_module"
