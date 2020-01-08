{
  'name':'JS Custom Reports',
  'summary': 'Personalización de los documentos impresos',
  'description': 'Modifica las vistas HTML de los documentos que después se pasan a PDF como pueden ser presupuestos y facturas.',
  'version':'1.0',
  'author':'Jim Sports',
  'data': [
    'views/layout.xml',
    'views/invoice.xml',
    'views/saleorder.xml',
    'views/deliveryslip.xml',
  ],
  'category': 'Advanced Reporting',
  'depends': ['base', 'delivery', 'sale', 'purchase',],
}