from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': (
        'fk__%(table_name)s__'
        '%(all_column_names)s__'
        '%(referred_table_name)s'
    ),
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

def init_db(app):
    db.init_app(app)

    with app.app_context():
        # importing models
        from app import models
        # creating database
        db.create_all()

        # creating tables if not exists
        if not models.Section.query.first():
            from app.utils import create_and_fill_out_tables
            create_and_fill_out_tables(models)
