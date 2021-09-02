from datetime import datetime

import pytest

from sqlalchemy.exc import IntegrityError

from aurweb import db
from aurweb.db import create, query, rollback
from aurweb.models.package_base import PackageBase
from aurweb.models.package_request import (ACCEPTED, ACCEPTED_ID, CLOSED, CLOSED_ID, PENDING, PENDING_ID, REJECTED,
                                           REJECTED_ID, PackageRequest)
from aurweb.models.request_type import RequestType
from aurweb.models.user import User
from aurweb.testing import setup_test_db

user = pkgbase = None


@pytest.fixture(autouse=True)
def setup():
    global user, pkgbase

    setup_test_db("PackageRequests", "PackageBases", "Users")

    with db.begin():
        user = create(User, Username="test", Email="test@example.org",
                      RealName="Test User", Passwd="testPassword")
        pkgbase = create(PackageBase, Name="test-package", Maintainer=user)


def test_package_request_creation():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    assert request_type.Name == "merge"

    with db.begin():
        package_request = create(PackageRequest, RequestType=request_type,
                                 User=user, PackageBase=pkgbase,
                                 PackageBaseName=pkgbase.Name,
                                 Comments=str(), ClosureComment=str())

    assert bool(package_request.ID)
    assert package_request.RequestType == request_type
    assert package_request.User == user
    assert package_request.PackageBase == pkgbase
    assert package_request.PackageBaseName == pkgbase.Name
    assert package_request.Comments == str()
    assert package_request.ClosureComment == str()

    # Make sure that everything is cross-referenced with relationships.
    assert package_request in request_type.package_requests
    assert package_request in user.package_requests
    assert package_request in pkgbase.requests


def test_package_request_closed():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    assert request_type.Name == "merge"

    ts = int(datetime.utcnow().timestamp())
    with db.begin():
        package_request = create(PackageRequest, RequestType=request_type,
                                 User=user, PackageBase=pkgbase,
                                 PackageBaseName=pkgbase.Name,
                                 Closer=user, ClosedTS=ts,
                                 Comments=str(), ClosureComment=str())

    assert package_request.Closer == user
    assert package_request.ClosedTS == ts

    # Test relationships.
    assert package_request in user.closed_requests


def test_package_request_null_request_type_raises_exception():
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRequest, User=user, PackageBase=pkgbase,
                   PackageBaseName=pkgbase.Name,
                   Comments=str(), ClosureComment=str())
    rollback()


def test_package_request_null_user_raises_exception():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRequest, RequestType=request_type,
                   PackageBase=pkgbase, PackageBaseName=pkgbase.Name,
                   Comments=str(), ClosureComment=str())
    rollback()


def test_package_request_null_package_base_raises_exception():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRequest, RequestType=request_type,
                   User=user, PackageBaseName=pkgbase.Name,
                   Comments=str(), ClosureComment=str())
    rollback()


def test_package_request_null_package_base_name_raises_exception():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRequest, RequestType=request_type,
                   User=user, PackageBase=pkgbase,
                   Comments=str(), ClosureComment=str())
    rollback()


def test_package_request_null_comments_raises_exception():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRequest, RequestType=request_type, User=user,
                   PackageBase=pkgbase, PackageBaseName=pkgbase.Name,
                   ClosureComment=str())
    rollback()


def test_package_request_null_closure_comment_raises_exception():
    request_type = query(RequestType, RequestType.Name == "merge").first()
    with pytest.raises(IntegrityError):
        with db.begin():
            create(PackageRequest, RequestType=request_type, User=user,
                   PackageBase=pkgbase, PackageBaseName=pkgbase.Name,
                   Comments=str())
    rollback()


def test_package_request_status_display():
    """ Test status_display() based on the Status column value. """
    request_type = query(RequestType, RequestType.Name == "merge").first()

    with db.begin():
        pkgreq = create(PackageRequest, RequestType=request_type,
                        User=user, PackageBase=pkgbase,
                        PackageBaseName=pkgbase.Name,
                        Comments=str(), ClosureComment=str(),
                        Status=PENDING_ID)
    assert pkgreq.status_display() == PENDING

    with db.begin():
        pkgreq.Status = CLOSED_ID
    assert pkgreq.status_display() == CLOSED

    with db.begin():
        pkgreq.Status = ACCEPTED_ID
    assert pkgreq.status_display() == ACCEPTED

    with db.begin():
        pkgreq.Status = REJECTED_ID
    assert pkgreq.status_display() == REJECTED

    with db.begin():
        pkgreq.Status = 124
    with pytest.raises(KeyError):
        pkgreq.status_display()
