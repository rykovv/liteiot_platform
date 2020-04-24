from psycopg2 import sql
from app.helpers.misc import with_psql

@with_psql
def create_datatable(cur, appkey, dev_id):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                utc NUMERIC(10) NOT NULL,
                timedate VARCHAR(100) NOT NULL,
                data json NOT NULL
            )"""
        ).format(sql.Identifier(tn)))
    return (True,)

    
@with_psql
def delete_datatable(cur, appkey, dev_id):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        psycopg2.sql.SQL(
            "DROP TABLE {}"
        ).format(sql.Identifier(tn)))
    return (True,)

@with_psql
def create_table(cur, appkey):
    tn = 'devices_' +str(appkey)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                name VARCHAR(30) NOT NULL,
                dev_id NUMERIC(3) PRIMARY KEY,
                description VARCHAR(200)
            )"""
        ).format(sql.Identifier(tn)))
    return (True,)

    
@with_psql
def delete_table(cur, appkey):
    tn = 'devices_' +str(appkey)
    cur.execute(
        psycopg2.sql.SQL(
            "DROP TABLE {}"
        ).format(sql.Identifier(tn)))
    return (True,)

@with_psql
def create(cur, name, dev_id, appkey, desc):
    tn = 'devices_' +str(appkey)
    query = """
    INSERT INTO 
        {}
    VALUES
        (%s, %s, %s)
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [name, dev_id, desc])
    return (True,)


@with_psql
def delete(cur, appkey, dev_id):
    tn = 'devices_' +str(appkey)
    query = """
    DELETE FROM 
        {}
    WHERE
        dev_id = %s
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [dev_id])
    return (True,)


@with_psql
def get(cur, appkey, dev_id):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT * FROM 
        {}
    WHERE
        dev_id = %s
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [dev_id])
    dev = cur.fetchone()
    
    if (dev is None):
        return (False, 'There is no device with dev_id = {}'.format(dev_id))
    else:
        return (True, dev)


@with_psql
def get_list(cur, appkey):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT * FROM 
        {}
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)))
    return (True, cur.fetchall())


@with_psql
def get_count(cur, appkey):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT COUNT(*) FROM 
        {}
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [appkey])
        
    return (True, cur.fetchone())

@with_psql
def get_device_table_names(cur):
    query = """
        SELECT table_name FROM
            information_schema.tables
        WHERE
            table_name ~ '^devices'
        """
    cur.execute(query, ())
    return(True, cur.fetchall())


def get_count_all():
    count = 0
    tns = get_device_table_names()
    if tns[0] and len(tns[1]) > 0:
        for tn in tns[1]:
           sp = tn[0].split('_')
           r = get_count(sp[1])
           if r[0]:
               count += r[1][0]

    return count
