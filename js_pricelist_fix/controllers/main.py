# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime
import csv
import os

class jsProductPricelist(http.Controller):
    @http.route([
        '/js_pricelist_fix'
    ], type='http', auth='user')
    def index(self, **kw):
        return request.render('js_pricelist_fix.pricelist_edit_index')

    @http.route([
        '/js_pricelist_fix/run'
    ], type='http', auth='user')
    def run(self, plimit=None, tmode=0, **kw):

        # Solo pueden acceder usuarios con permisos de configuración (Administración/Ajustes)
        if request.env.user.has_group('base.group_system'):

            product_model = request.env['product.template'].sudo()
            pricelist_model = request.env['product.pricelist'].sudo()
            pricelist_item_model = request.env['product.pricelist.item'].sudo()
            pricelists = pricelist_model.search([('name', '=', plimit)]) # Tarifas
            actual_date = datetime.now().strftime('%Y-%m-%d') # Fecha actual
            test_mode = int(tmode) # Test mode como entero (0-1)
            debug_processed = list() # Creamos una lista para guardar los valores

            # Eliminar precios antiguos de tarifas
            pricelist_item_model.search([("date_end", "<", actual_date)]).unlink()

            # Hacemos uso de request para acceder al modelo de los productos
            product_list = product_model.search([
                ('sale_ok', '=', True),
                ('default_code', '!=', False),
                ('type', '=', 'product')
            ], order='name')

            # Recorremos las tarifas
            for pricelist in pricelists:

                # Realizamos un bucle para recorrer los productos
                for product in product_list:

                    # Cada variante tiene precio/s
                    variant_rules = list()
                    # Columna "base" de cada variante
                    variant_bases = list()
                    # Columna "fixed_price" de cada variante
                    variant_prices = list()
                    # Columna "price_discount" de cada variante
                    variant_discounts = list()
                    # Columna "percent_price" de cada variante
                    variant_percents = list()
                    # Columna "price_surcharge" de cada variante
                    variant_surcharges = list()
                    # Columna "compute_price" de cada variante
                    variant_computes = list()
                    # Subresultado de cada comprobación
                    all_data_bool = list()
                    # "Recordset" con todas las reglas de las variantes
                    price_rules_recordset = pricelist_item_model.browse()

                    # Buscamos precios de las variantes
                    for variant in product.product_variant_ids:

                        # Precios de tarifa
                        prices_list = pricelist_item_model.search([
                            "&", "&", "&",
                            ["pricelist_id", "=", pricelist.id],
                            ["product_id", "=", variant.id],
                            "|", 
                            ["date_start", "=", False], 
                            ["date_start", "<", actual_date], 
                            "|", 
                            ["date_end","=",False], 
                            ["date_end", ">", actual_date]
                        ], order='id ASC')

                        # Guardamos True o False según tenga o no precio
                        variant_rules.append(True if prices_list else False)

                        # Recuperamos los datos
                        for rule in prices_list:
                            price_rules_recordset += rule
                            variant_bases.append(rule.base)
                            variant_prices.append(rule.fixed_price)
                            variant_discounts.append(rule.price_discount)
                            variant_percents.append(rule.percent_price)
                            variant_surcharges.append(rule.price_surcharge)
                            variant_computes.append(rule.compute_price)

                    # Comprobaciones sobre los datos
                    all_data_bool.append(variant_rules and all(variant_rules)) # Todas las variantes tienen precio
                    all_data_bool.append(variant_bases and all(x==variant_bases[0] for x in variant_bases))
                    all_data_bool.append(variant_prices and all(x==variant_prices[0] for x in variant_prices))
                    all_data_bool.append(variant_discounts and all(x==variant_discounts[0] for x in variant_discounts))
                    all_data_bool.append(variant_percents and all(x==variant_percents[0] for x in variant_percents))
                    all_data_bool.append(variant_surcharges and all(x==variant_surcharges[0] for x in variant_surcharges))
                    all_data_bool.append(variant_computes and all(x==variant_computes[0] for x in variant_computes))

                    # Si todos los datos coinciden
                    if all(all_data_bool):

                        # Si no estamos en modo de prueba
                        if not test_mode:
                            main_price_rule = price_rules_recordset[0].ensure_one()

                            new_rule = {
                                'fixed_price': main_price_rule.fixed_price,
                                'price_discount': main_price_rule.price_discount,
                                'date_start': main_price_rule.date_start,
                                'date_end': main_price_rule.date_end,
                                'currency_id': main_price_rule.currency_id.id,
                                'min_quantity': main_price_rule.min_quantity,
                                'compute_price': main_price_rule.compute_price,
                                'company_id': main_price_rule.company_id.id,
                                'create_uid': main_price_rule.create_uid.id,
                                'write_uid': main_price_rule.write_uid.id,
                                'pricelist_id': pricelist.id,
                                'applied_on': '1_product',
                                'product_tmpl_id': product.id
                            }

                            # Si "percent_price" no es 0
                            if main_price_rule.percent_price:
                                new_rule.update({ 'percent_price': main_price_rule.percent_price })

                            # Si "price_surcharge" no es 0
                            if main_price_rule.price_surcharge:
                                new_rule.update({ 'price_surcharge': main_price_rule.price_surcharge })

                            # Eliminamos los precios existentes en la plantilla
                            pricelist_item_model.search([
                                ('pricelist_id', '=', pricelist.id),
                                ('product_tmpl_id', '=', product.id)
                            ]).unlink()

                            # Creamos el precio para la plantilla (a partir de otro)
                            pricelist_item_model.create(new_rule)

                            # Eliminamos los precios de variantes
                            price_rules_recordset.unlink()

                        # Sacamos la información de los productos
                        debug_processed.append({
                            'id': product.id,
                            'reference': product.default_code.strip(),
                            'name': product.name,
                            'variants': len(product.product_variant_ids),
                            'prices_modified': str(variant_prices)
                        })

            # Pasamos los resultados a la vista
            return request.render('js_pricelist_fix.pricelist_edit_batch', {
                'total': len(product_list),
                'pricelists': str([p.name for p in pricelists]),
                'processed': len(debug_processed),
                'products': debug_processed
            })

        else:
            return 'No está autorizado para acceder a esta página'

    @http.route([
        '/js_pricelist_fix/update'
    ], type='http', auth='user')
    def run(self, filename=None, delimitier=';', tmode=0, **kw):

        # Solo pueden acceder usuarios con permisos de configuración (Administración/Ajustes)
        if request.env.user.has_group('base.group_system'):

            test_mode = int(tmode) # Test mode como entero (0-1)
            debug_processed = list() # Creamos una lista para guardar los valores
            root_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
            csv_path = os.path.join(root_folder, 'static', filename)

            with open(csv_path) as csv_file:
                product_model = request.env['product.template'].sudo()
                variant_model = request.env['product.product'].sudo()
                pricelist_model = request.env['product.pricelist'].sudo()
                pricelist_item_model = request.env['product.pricelist.item'].sudo()
                csv_reader = csv.reader(csv_file, delimiter=delimitier)
                csv_parsed = { 'pricelists': dict(), 'counter': 0 }

                for row in csv_reader:
                    # Actualizar el contador
                    csv_parsed['counter'] += 1

                    # Si es la primera línea
                    if csv_parsed.get('counter') == 1:
                        # Para cada columna
                        for col_name in row:
                            # Que no sea REF o DESCRIPTION
                            if col_name.upper() not in ('REF', 'DESCRIPTION'):
                                # Buscamos la lista de precios
                                pricelist = pricelist_model.search([('name', '=', col_name)], limit=1)
                                # La lista de precios existe
                                if pricelist:
                                    csv_parsed['pricelists'].update({ row.index(col_name):pricelist })

                    # Líneas restantes
                    else:
                        # Se buscan los productos por la primera columna (REFERENCIA)
                        product = product_model.search([('default_code', 'like', row[0])], limit=1)
                        variant = variant_model.search([('default_code', 'like', row[0])], limit=1)

                        results = dict()

                        for col_num, pricelist in csv_parsed['pricelists'].items():
                            if product:
                                # Borrar reglas antiguas
                                old_prices = pricelist_item_model.search([
                                    ('base', '=', 'list_price'),
                                    ('compute_price', '=', 'fixed'),
                                    ('applied_on', '=', '1_product'),
                                    ('pricelist_id', '=', pricelist.id),
                                    ('product_tmpl_id', '=', product.id)
                                ])

                                if not test_mode:
                                    # Crear nueva
                                    pricelist_item_model.create({
                                        'base': 'list_price',
                                        'compute_price': 'fixed',
                                        'applied_on': '1_product',
                                        'pricelist_id': pricelist.id,
                                        'product_tmpl_id': product.id,
                                        'fixed_price': float(row[col_num])
                                    })

                                # Información de debug
                                results[pricelist.name] = "%s >> [%s]" % ([p.fixed_price for p in old_prices], float(row[col_num]))

                                if not test_mode:
                                    # Borrar reglas antiguas
                                    old_prices.unlink()

                            elif variant:
                                # Borrar reglas antiguas
                                old_prices = pricelist_item_model.search([
                                    ('base', '=', 'list_price'),
                                    ('compute_price', '=', 'fixed'),
                                    ('applied_on', '=', '0_product_variant'),
                                    ('pricelist_id', '=', pricelist.id),
                                    ('product_id', '=', variant.id)
                                ])

                                if not test_mode:
                                    # Crear nueva
                                    pricelist_item_model.create({
                                        'base': 'list_price',
                                        'compute_price': 'fixed',
                                        'applied_on': '0_product_variant',
                                        'pricelist_id': pricelist.id,
                                        'product_id': product.id,
                                        'fixed_price': float(row[col_num])
                                    })

                                # Información de debug
                                results[pricelist.name] = "%s >> [%s]" % ([p.fixed_price for p in old_prices], float(row[col_num]))

                                if not test_mode:
                                    # Borrar reglas antiguas
                                    old_prices.unlink()
                        
                        # Información de debug
                        if product or variant:
                            isProduct = not variant and product
                            item = product or variant
                            prices_debug = str()

                            for l,s in results.items():
                                prices_debug += '<b>%s<b/><br/><pre>%s</pre>' % (l,s)

                            debug_processed.append({
                                'id': item.id,
                                'reference': "%s >> %s" % (row[0], item.default_code.strip()),
                                'name': item.name,
                                'variants': len(product.product_variant_ids) if isProduct else '-',
                                'prices_modified': prices_debug
                            })

            # Pasamos los resultados a la vista
            return request.render('js_pricelist_fix.pricelist_edit_batch', {
                'total': csv_parsed['counter'],
                'pricelists': str([p.name for p in csv_parsed['pricelists'].values()]),
                'processed': len(debug_processed),
                'products': debug_processed
            })

        else:
            return 'No está autorizado para acceder a esta página'