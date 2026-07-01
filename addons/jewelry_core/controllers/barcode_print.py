from odoo import http
from odoo.http import request


class BarcodePrintController(http.Controller):

    @http.route('/print/barcode/<int:product_id>', type='http', auth='user')
    def print_barcode(self, product_id):
        product = request.env['product.template'].browse(product_id).exists()
        if not product:
            return request.not_found()
        barcode_src = '/report/barcode/Code128/%s' % product.barcode if product.barcode else ''
        bc_text = product.barcode or ''
        return_url = '/web#id=%s&model=product.template&view_type=form' % product_id

        html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Barcode</title>
<style>
  @page { margin: 0; size: auto; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: sans-serif; }
  .label {
    display: inline-block;
    padding: 0 0 0 5mm;
  }
  img {
    display: block;
    height: 30px;
    width: auto;
  }
  .bc-text {
    font-family: monospace;
    font-size: 7px;
    text-align: center;
    color: #333;
  }
  @media print {
    body { min-height: auto; }
  }
</style>
</head>
<body>
  <div class="label">
    <img src="__BARCODE_SRC__" alt="barcode"/>
    <div class="bc-text">__BC_TEXT__</div>
  </div>
  <script>
    var returnUrl = "__RETURN_URL__";
    window.addEventListener("load", function() {
      setTimeout(function() {
        window.print();
        window.addEventListener("afterprint", function() {
          window.location.href = returnUrl;
        });
        setTimeout(function() { window.location.href = returnUrl; }, 5000);
      }, 500);
    });
  </script>
</body>
</html>'''
        html = html.replace('__BARCODE_SRC__', barcode_src)
        html = html.replace('__BC_TEXT__', bc_text)
        html = html.replace('__RETURN_URL__', return_url)

        return request.make_response(html, [('Content-Type', 'text/html')])
