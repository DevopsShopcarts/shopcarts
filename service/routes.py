# spell: ignore Rofrano jsonify restx dbname
"""
Shopcart Store Service with Swagger
Paths:
------
GET / - Displays a UI for Selenium testing
GET /shopcarts - Returns a list all of the Shopcarts
GET /shopcarts/{id} - Returns the Shopcart with a given id number
POST /shopcarts - creates a new Shopcart record in the database
PUT /shopcarts/{id} - updates a Shopcart record in the database
DELETE /shopcarts/{id} - deletes a Shopcart record in the database
"""

import logging
from flask import request, abort
from flask_restx import Resource, fields
from service.models import Product, Shopcart
from service.utils import status  # HTTP Status Codes
from . import app, api

######################################################################
# Configure the Root route before OpenAPI
######################################################################


@app.route("/")
def index():
    """Index page"""
    return app.send_static_file("index.html")


create_model = api.model(
    "Product",
    {
        "name": fields.String(required=True, description="The name of the Product"),
        "quantity": fields.Float(
            required=True, description="The quantity of the Product"
        ),
        "price": fields.Float(required=True, description="The price of the Product"),
        "shopcart_id": fields.Integer(
            required=True, description="The shop cart id of the product"
        ),
    },
)


product_model = api.model(
    "Product",
    # create_model,
    {
        "id": fields.Integer(
            readOnly=True, description="The unique id assigned internally by service"
        ),
        "name": fields.String(required=True, description="The name of the Product", maxLength=260),
        "quantity": fields.Integer(
            required=True, description="The quantity of the Product"
        ),
        "price": fields.Float(required=True, description="The price of the Product"),
        "shopcart_id": fields.Integer(
            required=True, description="The shop cart id of the product"
        ),
    }
)
shopcart_model = api.model(
    "ShopcartModel",
    {
        "id": fields.Integer(required=True, description="The id of the customer"),
        "products": fields.List(
            fields.Nested(product_model, required=True),
            required=True,
            description="The list of products in the shop cart",
        ),
    },
)

product_parser = api.parser()
product_parser.add_argument('id', type=int)
product_parser.add_argument('name', type=str)
product_parser.add_argument('quantity', type=int)
product_parser.add_argument('price', type=float)
product_parser.add_argument('shopcart_id', type=int)

shopcart_parser = api.parser()
shopcart_parser.add_argument('id', type=int)
shopcart_parser.add_argument('products', type=list)

######################################################################
#  PATH: /shopcarts/{id}
######################################################################


@api.route("/shopcarts/<id>")
@api.param("id", "The Shop Cart identifier")
class ShopCartResource(Resource):
    """
    ShopCartResource class
    Allows the manipulation of a single Shop Cart
    GET /shopcart{id} - Returns a Shop Cart with the id
    PUT /shopcart{id} - Update a Shop Cart with the id
    DELETE /shopcart{id} -  Deletes a Shop Cart with the id
    POST /shopcart{id} -  Create a Shop Cart with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A Shop Cart
    # ------------------------------------------------------------------
    @api.doc("get_shopcarts")
    @api.response(404, "Shop Cart not found")
    @api.marshal_with(shopcart_model)
    def get(self, id):
        """
        Retrieve a single Shop Cart
        This endpoint will return a Shop Cart based on it's id
        """
        app.logger.info("Request to Retrieve a shop cart with id [%s]", id)
        shopcart = Shopcart.find_by_id(id)
        if not shopcart:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Shop Cart with id '{}' was not found.".format(id),
            )
        return shopcart.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING Shop Cart
    # ------------------------------------------------------------------
    @api.doc("update_shopcarts")
    @api.response(404, "Shop Cart not found")
    @api.response(400, "The posted Shop Cart data was not valid")
    @api.expect(shopcart_parser, validate=True)
    @api.marshal_with(shopcart_model)
    def put(self, id):
        """
        Update a Shop Cart
        This endpoint will update a Shop Cart based the body that is posted
        """
        shopcart_parser.parse_args()
        app.logger.info("Request to Update a Shop Cart with id [%s]", id)
        shopcart = Shopcart.find_by_id(id)
        if not shopcart:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Shop Cart with id '{}' was not found.".format(id),
            )
        app.logger.debug("Payload = %s", api.payload)
        data = api.payload
        shopcart.deserialize(data)
        shopcart.id = id
        shopcart.update()
        return shopcart.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A Shop Cart
    # ------------------------------------------------------------------
    @api.doc("delete_shopcarts")
    @api.response(204, "Shop Cart deleted")
    def delete(self, id):
        """
        Delete a Shop Cart
        This endpoint will delete a Shop Cart based the id specified in the path
        """
        app.logger.info("Request to Delete a shopcart with id [%s]", id)
        shopcart = Shopcart.find_by_id(id)
        if shopcart:
            shopcart.delete()
            app.logger.info("Shop Cart with id [%s] was deleted", id)
        return "", status.HTTP_204_NO_CONTENT

    # ------------------------------------------------------------------
    # Create A NEW Shop Cart
    # ------------------------------------------------------------------
    @api.doc("create_shopcarts")
    @api.response(400, "The posted data was not valid")
    @api.response(409, "Shop Cart already exists")
    @api.expect(shopcart_parser, validate=True)
    @api.marshal_with(shopcart_model, code=201)
    def post(self, id):
        """
        Creates a Shop Cart
        This endpoint will create a Shop Cart based the data in the body that is posted
        """
        shopcart_parser.parse_args()
        app.logger.info("Request to Create a Shop Cart")
        shopcart = Shopcart()
        app.logger.debug("Payload = %s", api.payload)
        shopcart.deserialize(api.payload)
        found_shop_cart = Shopcart.find_by_id(id)
        logging.info("To create shopcart with id: %d", shopcart.id)
        if found_shop_cart is not None:
            logging.info("Found shopcart: %s", type(found_shop_cart))
            abort(status.HTTP_409_CONFLICT, f"Shopcart {shopcart.id} already exists")
        shopcart.create(id)
        app.logger.info("shopcart with new id [%s] created!", id)
        location_url = api.url_for(ShopCartResource, id=shopcart.id, _external=True)
        return shopcart.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# RETRIEVE A SHOP CART
######################################################################
'''
@app.route("/shopcarts/<int:id>", methods=["GET"])
def get_shopcarts(id):
    """
    Retrieve a shopcart of a customer
    This endpoint will return a shopcart based on it's id
    """
    app.logger.info("Request for Shopcart with id: %s", id)
    shopcart = Shopcart.find_by_id(id)
    if not shopcart:
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Shopcart with id '{id}' could not be found.",
        )

    return make_response(jsonify(shopcart.serialize()), status.HTTP_200_OK)


######################################################################
# UPDATE AN EXISTING SHOPCART
######################################################################
@app.route("/shopcarts/<int:id>", methods=["PUT"])
def update_shopcarts(id):
    """
    Update a Shopcart
    This endpoint will update a Shopcart based the body that is posted
    """
    app.logger.info("Request to Update a Shop Cart with id [%s]", id)
    check_content_type("application/json")

    shopcart = Shopcart.find_by_id(id)
    if not shopcart:
        abort(status.HTTP_404_NOT_FOUND, f"Shopcart with id '{id}' was not found.")

    data = request.get_json()
    app.logger.info(data)
    shopcart.deserialize(data)
    shopcart.id = id
    shopcart.update()
    return make_response(jsonify(shopcart.serialize()), status.HTTP_200_OK)


######################################################################
# DELETE A SHOPCART
######################################################################
@app.route("/shopcarts/<int:id>", methods=["DELETE"])
def delete_shopcarts(id):
    """
    Delete a Shopcart
    This endpoint will delete a Shopcart based the id specified in the path
    """
    app.logger.info("Request to delete shopcart with id: %s", id)
    shopcart = Shopcart.find_by_id(id)
    if shopcart:
        shopcart.delete()
    return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
# CREATE A NEW SHOP CART
######################################################################
@app.route("/shopcarts/<int:id>", methods=["POST"])
def create_shopcarts(id):
    """
    Creates a Shopcart
    This endpoint will create a Shop Cart based the data in the body that is posted
    """
    app.logger.info("Request to create a Shop Cart")
    check_content_type("application/json")
    shopcart = Shopcart()
    shopcart.deserialize(request.get_json())
    found_shop_cart = Shopcart.find_by_id(shopcart.id)
    logging.info("To create shopcart with id: %d", shopcart.id)
    if found_shop_cart is not None:
        logging.info("Found shopcart: %s", type(found_shop_cart))
        abort(status.HTTP_409_CONFLICT, f"Shopcart {shopcart.id} already exists")
    shopcart.create(id)
    message = Shopcart.find_by_id(shopcart.id).serialize()
    location_url = url_for("get_shopcarts", id=shopcart.id, _external=True)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )
'''

######################################################################
#  PATH: /shopcarts/{id}/products/{product_id}
######################################################################


@api.route("/shopcarts/<id>/products/<product_id>")
@api.param("id", "The shop cart identifier")
@api.param("product_id", "The product identifier")
class ProductResource(Resource):
    # ------------------------------------------------------------------
    # RETRIEVE A Product
    # ------------------------------------------------------------------
    @api.doc("get_products")
    @api.response(404, "Product not found")
    @api.marshal_with(product_model)
    def get(self, id, product_id):
        """
        Retrieve a single Product
        This endpoint will return a Product based on it's id
        """
        app.logger.info(
            "Request to Retrieve a Product with id [%s] for Customer with id [%s]",
            product_id,
            id,
        )
        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Product with id '{}' was not found.".format(product_id),
            )
        return product.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A Product
    # ------------------------------------------------------------------
    @api.doc("delete_products")
    @api.response(204, "Product deleted")
    def delete(self, id, product_id):
        """
        Delete a Product
        This endpoint will delete a Product based the id specified in the path
        """
        app.logger.info(
            "Request to Delete a Product with id [%s] for customer with id [%s]",
            product_id,
            id,
        )
        product = Product.find(product_id)
        if product:
            product.delete()
            app.logger.info("Product with id [%s] was deleted", product_id)
        return "", status.HTTP_204_NO_CONTENT

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING Product
    # ------------------------------------------------------------------
    @api.doc("update_products")
    @api.response(404, "Product not found")
    @api.response(400, "The posted Product data was not valid")
    @api.expect(product_parser, validate=True)
    @api.marshal_with(product_model)
    def put(self, id, product_id):
        """
        Update a Product
        This endpoint will update a Product based the body that is posted
        """
        args = product_parser.parse_args()
        app.logger.info(
            "Request to Update a Product with id [%s] for customer with id [%s]",
            product_id,
            id,
        )
        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Product with id '{}' was not found.".format(product_id),
            )
        app.logger.debug("Payload = %s", api.payload)
        # data = api.payload
        product.deserialize(args)
        product.id = product_id
        product.update()
        return product.serialize(), status.HTTP_200_OK


######################################################################
#  PATH: /shopcarts/{id}/products
######################################################################
@api.route("/shopcarts/<id>/products")
@api.param("id", "The shop cart identifier")
class ProductOperation(Resource):
    # ------------------------------------------------------------------
    # LIST ALL ProductS
    # ------------------------------------------------------------------
    @api.doc("list_products")
    @api.response(404, "Shop Cart not found")
    @api.marshal_list_with(product_model)
    def get(self, id):
        """Returns the list of products in the shopcart"""
        app.logger.info("Request to list Products...")
        shopcart = Shopcart().find_by_id(id)
        if not shopcart:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Shop Cart with id '{}' was not found.".format(id),
            )
        results = [product.serialize() for product in shopcart.products]
        app.logger.info("[%s] Products returned", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # Add A NEW Product to the shopcart
    # ------------------------------------------------------------------
    @api.doc("add_products")
    @api.response(400, "The posted data was not valid")
    @api.response(404, "Product not found")
    @api.expect(product_parser, validate=True)
    @api.marshal_with(product_model, code=201)
    def post(self, id):
        """
        Creates a Product
        This endpoint will create a Product and add it to the shopcart based the data in the body that is posted
        """
        product_parser.parse_args()
        app.logger.info("Request to Create a Product")
        shopcart = Shopcart().find_by_id(id)
        if not shopcart:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Shop Cart with id '{}' was not found.".format(id),
            )
        product = Product()
        app.logger.debug("Payload = %s", api.payload)
        data = api.payload
        product.deserialize(data)
        shopcart.products.append(product)
        shopcart.update()
        return product.serialize(), status.HTTP_201_CREATED


'''
######################################################################
# LIST ALL PRODUCTS OF A GIVEN SHOP CART
######################################################################
@app.route("/shopcarts/<int:id>/products", methods=["GET"])
def list_products(id):
    """Return all of products of a given shopcart"""
    app.logger.info("Request for reading items of a given shop cart")
    shopcart = Shopcart().find_by_id(id)
    # If the shopcart does not exist, return 400 BAD REQUEST ERROR
    if not shopcart:
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Shopcart with id '{id}' could not be found.",
        )
    results = [product.serialize() for product in shopcart.products]
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# RETRIEVE AN PRODUCT FROM SHOPCART
######################################################################
@app.route("/shopcarts/<int:id>/products/<int:product_id>", methods=["GET"])
def get_products(id, product_id):
    """
    Get an Address
    This endpoint returns just an address
    """
    app.logger.info(
        "Request to retrieve Product %s for CUSTOMER id: %s", (product_id, id)
    )

    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Shopcart with id '{product_id}' could not be found.",
        )

    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)


######################################################################
# ADD A Product TO A shopcart
######################################################################
@app.route("/shopcarts/<int:id>/products", methods=["POST"])
def add_products(id):
    """
    Create a Product on a Shopcart
    This endpoint will add a product to a shopcart
    """
    app.logger.info("Request to create a Products for Shopcart with id: %s", id)
    check_content_type("application/json")

    shopcart = Shopcart().find_by_id(id)
    if not shopcart:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Shopcart with id '{id}' could not be found.",
        )

    product = Product()
    product.deserialize(request.get_json())
    shopcart.products.append(product)
    shopcart.update()
    message = product.serialize()
    return make_response(jsonify(message), status.HTTP_201_CREATED)


######################################################################
# DELETE A Product
######################################################################
@app.route("/shopcarts/<int:id>/products/<int:product_id>", methods=["DELETE"])
def delete_products(id, product_id):
    """
    Delete a Product
    This endpoint will delete a Product based the id specified in the path
    """
    app.logger.info(
        "Request to delete Product %s for Customer id: %s", (product_id, id)
    )

    product = Product().find(product_id)
    if product:
        product.delete()

    return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
# UPDATE A Product
######################################################################
@app.route(
    "/shopcarts/<int:id>/products/<int:product_id>",
    methods=["PUT"],
)
def update_products(id, product_id):
    """
    Update a Product
    This endpoint will update a product based the body that is posted
    """
    app.logger.info(
        "Request to update product %s for customer id: %s", (product_id, id)
    )
    check_content_type("application/json")

    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product with id '{product_id}' could not be found.",
        )

    product.deserialize(request.get_json())
    product.id = product_id
    product.update()
    return make_response(jsonify(product.serialize()), status.HTTP_200_OK)

'''
######################################################################
#  PATH: /shopcarts
######################################################################


@api.route("/shopcarts", strict_slashes=False)
class ShopcartCollection(Resource):
    # ------------------------------------------------------------------
    # LIST ALL Shop carts
    # ------------------------------------------------------------------
    @api.doc("list_shopcarts")
    @api.marshal_list_with(shopcart_model)
    def get(self):
        """Returns all of the Shopcarts"""
        app.logger.info("Request for Shop Cart list")
        id = request.args.get("id")
        name = request.args.get("name")
        results = []
        if name:
            app.logger.info("Request to Retrieve a shop cart with id [%s]", id)
            shopcarts = Shopcart.filter_by_product_name(name)
            results = [shopcart.serialize() for shopcart in shopcarts]
        else:
            shopcarts = Shopcart.all()
            results = [shopcart.serialize() for shopcart in shopcarts]
        return results, status.HTTP_200_OK


'''
@app.route("/shopcarts", methods=["GET"])
def list_shopcarts():
    """Returns all of the Shopcarts"""
    app.logger.info("Request for Shop Cart list")
    id = request.args.get("id")
    results = []
    if id:
        shopcarts = Shopcart.find_by_id(id)
        results = [shopcarts.serialize()]
    else:
        shopcarts = Shopcart.all()
        results = [shopcart.serialize() for shopcart in shopcarts]
    return make_response(jsonify(results), status.HTTP_200_OK)
'''
######################################################################
#  PATH: /shopcarts/{id}/clear
######################################################################


@api.route("/shopcarts/<id>/clear")
@api.param("id", "The shop cart identifier")
class ShopcartAction(Resource):
    # ------------------------------------------------------------------
    # clear a shopcart
    # ------------------------------------------------------------------
    @api.doc("update_shopcarts")
    @api.response(404, "Shop Cart not found")
    @api.response(400, "The posted Shop Cart data was not valid")
    @api.expect(shopcart_parser, validate=True)
    @api.marshal_with(shopcart_model)
    def put(self, id):
        """
        Update a Shop Cart
        This endpoint will update a Shop Cart based the body that is posted
        """
        app.logger.info("Request to Update a Shop Cart with id [%s]", id)
        shopcart_parser.parse_args()
        shopcart = Shopcart.find_by_id(id)
        if not shopcart:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Shop Cart with id '{}' was not found.".format(id),
            )
        for product in shopcart.products:
            product.delete()
        shopcart.products = []
        shopcart.id = id
        shopcart.update()
        return shopcart.serialize(), status.HTTP_200_OK


'''
@app.route("/shopcarts/<int:id>/clear", methods=["PUT"])
def clear_shopcarts(id):
    """Clear a shop cart according to customer id"""
    app.logger.info("Request to clear shop cart for customer id: %s", (id))
    check_content_type("application/json")

    shopcart = Shopcart.find_by_id(id)
    if not shopcart:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Shopcart with id '{id}' could not be found.",
        )
    for product in shopcart.products:
        product.delete()
    shopcart.products = []
    shopcart.id = id
    shopcart.update()
    return make_response(jsonify(shopcart.serialize()), status.HTTP_200_OK)

'''
'''
######################################################################
#  PATH: /shopcarts?product_name = <name>
######################################################################


@api.route("/shopcarts?product_name = <name>")
@api.param("name", "The name of the product")
class ShopcartQuery(Resource):
    # ------------------------------------------------------------------
    # Filter and Get a list of shop carts
    # ------------------------------------------------------------------
    @api.doc("filter_shopcarts")
    @api.marshal_list_with(shopcart_model)
    def get(self, name):
        """
        Retrieve a single Shop Cart
        This endpoint will return a Shop Cart based on it's id
        """
        app.logger.info("Request to Retrieve a shop cart with id [%s]", id)
        shopcarts = Shopcart.filter_by_product_name(name)
        results = [shopcart.serialize() for shopcart in shopcarts]
        return results, status.HTTP_200_OK



######################################################################
# FILTER SHOP CARTS GIVEN A PRODUCT
######################################################################
@app.route(
    "/shopcarts/products/<string:product_name>",
    methods=["GET"],
)
def filter_shopcarts_by_product_name(product_name):
    """Return all shopcarts which contain the given product"""
    app.logger.info("Request for Shop Carts with given product")
    shopcarts = Shopcart.filter_by_product_name(product_name)
    results = [shopcart.serialize() for shopcart in shopcarts]
    return make_response(jsonify(results), status.HTTP_200_OK)
'''

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Content-Type must be {}".format(media_type),
    )


def init_db():
    """Initialize the model"""
    Shopcart.init_db(app)
