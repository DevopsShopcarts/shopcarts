"""
TestYourResourceModel API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from service import app
from service.models import db, Shopcart, Product
from service.utils import status  # HTTP Status Codes
from tests.factories import ShopCartFactory, ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/shopcarts"
PRODUCT_URL = "/product"
######################################################################
#  T E S T   C A S E S
######################################################################


class TestShopcartService(TestCase):
    """Shop Cart Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Shopcart.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""
        pass

    def setUp(self):
        """Runs before each test"""
        db.session.query(Product).delete()
        db.session.query(Shopcart).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_shopcarts(self, count):
        """Factory method to create shopcarts in bulk"""
        shopcarts = []
        for _ in range(count):
            shopcart = ShopCartFactory()
            resp = self.client.post(BASE_URL, json=shopcart.serialize())
            self.assertEqual(
                resp.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Shopcart",
            )
            new_shopcart = resp.get_json()
            shopcart.id = new_shopcart["id"]
            shopcarts.append(shopcart)
        return shopcarts

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the Home Page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_account(self):
        """It should Read a single Shopcart"""
        # get the id of an account
        shopcart = self._create_shopcarts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{shopcart.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["customer_id"], shopcart.customer_id)

    def test_get_account_not_found(self):
        """It should not Read an Account that is not found"""
        resp = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_shopcart(self):
        """It should Create a new Shopcart"""
        shopcart = ShopCartFactory()
        resp = self.client.post(
            BASE_URL, json=shopcart.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_shopcart = resp.get_json()
        self.assertEqual(
            new_shopcart["customer_id"], shopcart.customer_id, "Names does not match"
        )
        self.assertEqual(
            new_shopcart["products"], shopcart.products, "Address does not match"
        )

        # Check that the location header was correct by getting it
        resp = self.client.get(location, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_shopcart = resp.get_json()
        self.assertEqual(
            new_shopcart["customer_id"], shopcart.customer_id, "Names does not match"
        )
        self.assertEqual(
            new_shopcart["products"], shopcart.products, "Address does not match"
        )

    def test_add_product(self):
        """It should Create a new product"""
        shopcart = ShopCartFactory()
        resp = self.client.post(
            BASE_URL, json=shopcart.serialize(), content_type="application/json"
        )
        shopcart = Shopcart()
        shopcart.deserialize(resp.get_json())
        product = ProductFactory()
        product.shopcart_id = shopcart.id
        logging.info("The new product is: %s" % product.serialize())
        logging.info("The new shopcart is: %s" % shopcart.serialize())
        resp = self.client.post(
            PRODUCT_URL, json=product.serialize(), content_type="application/json"
        )
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)
        new_shopcart = Shopcart()
        new_shopcart.deserialize(resp.get_json())
        logging.info("The new shopcart is: %s", resp.get_json())
        self.assertEqual(new_shopcart.products[0].serialize(), product.serialize(), "Product does not match")

    def test_get_shopcart_list(self):
        """It should Get a list of shopcarts"""
        self._create_shopcarts(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_get_shopcart_by_customer_id(self):
        """It should Get a shop cart by customer id"""
        shopcarts = self._create_shopcarts(3)
        resp = self.client.get(
            BASE_URL, query_string=f"customer_id={shopcarts[1].customer_id}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[0]["customer_id"], shopcarts[1].customer_id)
