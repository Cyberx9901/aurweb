import aurweb.db


def setup_test_db(*args):
    """ This function is to be used to setup a test database before
    using it. It takes a variable number of table strings, and for
    each table in that set of table strings, it deletes all records.

    The primary goal of this method is to configure empty tables
    that tests can use from scratch. This means that tests using
    this function should make sure they do not depend on external
    records and keep their logic self-contained.

    Generally used inside of pytest fixtures, this function
    can be used anywhere, but keep in mind its functionality when
    doing so.

    Examples:
        setup_test_db("Users", "Sessions")

        test_tables = ["Users", "Sessions"];
        setup_test_db(*test_tables)
    """
    # Make sure that we've grabbed the engine before using the session.
    aurweb.db.get_engine()

    tables = list(args)
    for table in tables:
        aurweb.db.session.execute(f"DELETE FROM {table}")

    # Expunge all objects from SQLAlchemy's IdentityMap.
    aurweb.db.session.expunge_all()