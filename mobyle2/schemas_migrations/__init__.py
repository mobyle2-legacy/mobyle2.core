from copy import deepcopy
import sqlalchemy as s
from sqlalchemy.schema import Table
from migrate.changeset.constraint import ForeignKeyConstraint

def recreate_table_fkeys(table, session,):
    """Recreate all foreign keys in the table or declarative object"""
    if not isinstance(table, Table):
        table = table.__table__
    migrate_engine = session.bind
    metadata = table.metadata
    r_meta = s.MetaData(migrate_engine, True)
    def commit():
        session.commit()
        r_meta.bind.execute  ('COMMIT;')
        metadata.bind.execute('COMMIT;')
    fks = []
    commit()
    t = table
    rt = r_meta.tables[t.name]
    rt_constraints = [a for a in rt.foreign_keys]
    for cs in deepcopy(t.foreign_keys):
        if cs.__class__.__name__ == 'ForeignKey':
            table, column = cs.target_fullname.split('.')
            target = [r_meta.tables[table].c[column]]
            parent_table = r_meta.tables[cs.parent.table.name]
            parent = [parent_table.c[cs.parent.name]]
            fk = ForeignKeyConstraint(columns=parent,refcolumns=target)
            fk.use_alter = cs.use_alter
            fk.ondelete = 'CASCADE'
            fk.onupdate = 'CASCADE'
            fk.name = cs.name
            fks.append(fk)
            if (cs.name in [a.name for a in rt_constraints]
                or (cs.target_fullname
                    in [a.target_fullname for a in rt_constraints])):
                try:
                    fk.drop(migrate_engine)
                    commit()
                except:pass
    for fk in fks:
        fk.create(migrate_engine)
        commit()


