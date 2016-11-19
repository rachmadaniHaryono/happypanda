"""models for database."""
from peewee import (
    SqliteDatabase,
    TextField,
    Model,
    FloatField,
    IntegerField,
    BlobField,
    PrimaryKeyField,
    ForeignKeyField,


)

try:
    from database.db_constants import DB_PATH
except ImportError:
    from .database.db_constants import DB_PATH

database = SqliteDatabase(DB_PATH, **{})


class UnknownField(object):
    """Unknown field."""

    def __init__(self, *_, **__):
        """init func."""
        pass


class BaseModel(Model):
    """Base model."""

    class Meta:
        database = database


class Series(BaseModel):
    """Series."""

    artist = TextField(null=True)
    date_added = TextField(null=True)
    db_v = FloatField(null=True)
    exed = IntegerField()
    fav = IntegerField(null=True)
    info = TextField(null=True)
    is_archive = IntegerField(null=True)
    language = TextField(null=True)
    last_read = TextField(null=True)
    link = BlobField(null=True)
    path_in_archive = BlobField(null=True)
    profile = BlobField(null=True)
    pub_date = TextField(null=True)
    rating = IntegerField()
    series = PrimaryKeyField(db_column='series_id', null=True)
    series_path = BlobField(null=True)
    status = TextField(null=True)
    times_read = IntegerField(null=True)
    title = TextField(null=True)
    type = TextField(null=True)
    view = IntegerField(null=True)

    class Meta:
        db_table = 'series'


class Chapters(BaseModel):
    """chapters."""

    chapter = PrimaryKeyField(db_column='chapter_id', null=True)
    chapter_number = IntegerField(null=True)
    chapter_path = BlobField(null=True)
    chapter_title = TextField()
    in_archive = IntegerField(null=True)
    pages = IntegerField(null=True)
    series = ForeignKeyField(db_column='series_id', null=True, rel_model=Series, to_field='series')

    class Meta:
        db_table = 'chapters'


class Hashes(BaseModel):
    """hashes."""

    chapter = ForeignKeyField(
        db_column='chapter_id', null=True, rel_model=Chapters, to_field='chapter')
    hash = BlobField(null=True)
    hash_id = PrimaryKeyField(null=True)
    page = IntegerField(null=True)
    series = ForeignKeyField(db_column='series_id', null=True, rel_model=Series, to_field='series')

    class Meta:
        db_table = 'hashes'
        indexes = (
            (('hash', 'series', 'chapter', 'page'), True),
        )


class List(BaseModel):
    """list."""

    enforce = IntegerField(null=True)
    l_case = IntegerField(null=True)
    list_filter = TextField(null=True)
    list = PrimaryKeyField(db_column='list_id', null=True)
    list_name = TextField()
    profile = BlobField(null=True)
    regex = IntegerField(null=True)
    strict = IntegerField(null=True)
    type = IntegerField(null=True)

    class Meta:
        db_table = 'list'


class Namespaces(BaseModel):
    """namespaces."""

    namespace = TextField(unique=True)
    namespace_id = PrimaryKeyField(null=True)

    class Meta:
        db_table = 'namespaces'


class SeriesListMap(BaseModel):
    """series list map."""

    list = ForeignKeyField(db_column='list_id', rel_model=List, to_field='list')
    series = ForeignKeyField(db_column='series_id', rel_model=Series, to_field='series')

    class Meta:
        db_table = 'series_list_map'
        indexes = (
            (('list', 'series'), True),
        )


class Tags(BaseModel):
    """tags."""

    tag = TextField(unique=True)
    tag_id = PrimaryKeyField(null=True)

    class Meta:
        db_table = 'tags'


class TagsMappings(BaseModel):
    """tags mappings."""

    namespace = ForeignKeyField(
        db_column='namespace_id', null=True, rel_model=Namespaces, to_field='namespace_id')
    tag = ForeignKeyField(db_column='tag_id', null=True, rel_model=Tags, to_field='tag_id')
    tags_mappings = PrimaryKeyField(db_column='tags_mappings_id', null=True)

    class Meta:
        db_table = 'tags_mappings'
        indexes = (
            (('namespace', 'tag'), True),
        )


class SeriesTagsMap(BaseModel):
    """series tags map."""

    series = ForeignKeyField(
        db_column='series_id', null=True, rel_model=Series, to_field='series')
    tags_mappings = ForeignKeyField(
        db_column='tags_mappings_id', null=True, rel_model=TagsMappings, to_field='tags_mappings')

    class Meta:
        db_table = 'series_tags_map'
        indexes = (
            (('series', 'tags_mappings'), True),
        )


class SqliteStat1(BaseModel):
    """sqlite stat1."""

    idx = UnknownField(null=True)
    stat = UnknownField(null=True)
    tbl = UnknownField(null=True)

    class Meta:
        db_table = 'sqlite_stat1'


class Version(BaseModel):
    """version."""

    version = FloatField(null=True)

    class Meta:
        db_table = 'version'
