
# -*- coding: utf-8 -*-
from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class JsWebTemplateWebsiteSale(WebsiteSale):
    # Para corregir problema al mostrar el precio del producto
    # https://trello.com/c/EtrtWRyi/72-odoo-modifica-el-precio-del-producto-al-a%C3%B1adir-o-quitar-unidades-en-el-sitio-web
    @http.route(['/shop/get_unit_price'], type='json', auth="public", methods=['POST'], website=True)
    def get_unit_price(self, product_ids, add_qty, **kw):
        products = request.env['product.product'].with_context({'quantity': add_qty}).browse(product_ids)
        # return {product.id: product.website_price / add_qty for product in products}
        return {product.id: product.website_price for product in products}