# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class jsProductPricelist(http.Controller):
    @http.route([
        '/js_product_pricelist'
    ], type='http', auth='user')
    def index(self, **kw):
        return request.render('js_product_pricelist.pricelist_edit_index')

    @http.route([
        '/js_product_pricelist/run'
    ], type='http', auth='user')
    def run(self, plimit=0, **kw):

        # Solo pueden acceder usuarios con permisos de configuración (Administración/Ajustes)
        if request.env.user.has_group('base.group_system'):

            # Limite de productos como entero
            product_limit = int(plimit)

            # Creamos una lista para guardar los valores
            debug_processed = []

            # Hacemos uso de request para acceder al modelo de los productos
            product_list = request.env['product.template'].sudo().search([
                ('sale_ok', '=', True),
                ('default_code', '!=', False),
                ('type', '=', 'product')
            ], order='name')

            # Realizamos un bucle para descargar las imágenes y guardar los resultados
            for product in product_list:

                # Si no tiene variantes
                if (len(product.product_variant_ids) < 2):

                    # Buscamos los precios
                    prices_list = request.env['product.pricelist.item'].sudo().search([
                        ('product_id', '=', product.product_variant_ids[0].id)
                    ])

                    # Actualizamos los precios
                    for price_item in prices_list:
                        price_item.write({
                            'applied_on':'1_product',
                            'product_id':None,
                            'product_tmpl_id':product.id
                        })

                    # Sacamos la información de los productos actualizados
                    debug_processed.append({
                        'id': product.id,
                        'reference': product.default_code.strip(),
                        'name': product.name,
                        'prices_modified': len(prices_list)
                    })

                    # Si llegamos al límite de productos establecido salimos del bucle
                    if (product_limit > 0 and len(debug_processed) >= product_limit):
                        break

            # Pasamos los resultados a la vista
            return request.render('js_product_pricelist.pricelist_edit_batch', {
                'total': len(debug_processed),
                'products': debug_processed
            })

        else:
            return 'No está autorizado para acceder a esta página'
