from flask import Flask, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from PIL import Image
app = Flask(__name__)


#CORS(app)
# Configure logging
# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

class TesterReportes():

    def __init__(self):
        print("-------------------------- DEBUG 0 --------------------------------")
        super().__init__()
        self.datos = []
        self.datosUsu = []
        self.datosResuCer = []
        self.datosFichaCer = []
        self.maskCuenta = "0000000"
        self.maskNorComp = "0000-00000000"
        self.maskCosecha = "0000"
        print("Connection to MySQL ===================.")


    def generarReportes(self, file_path, parameters, reporte):
        print("::: Iniciando generarReportes() :::")
        print("<--------------------------| DEBUG 1 |-------------------------------->")
        hoy = datetime.today().date()

        #traigo datos de la empresa


        prefijoEmpresa = "05"
        nombreEmpresa = "marga"
        descripcionEmpresa = ""
        domicilioEmpresa =""
        cuitEmpresa = 20234762266
        empresaSituacionIva = 3




    # Example usage

    def main(self, parameters, reporteCodigo):
        print("------> ")
        self.generarReportes("reporte_" + str(reporteCodigo) + ".pdf", parameters, reporteCodigo)


@app.route('/dummy', methods=['GET'])
def dummy():
    import json




    data = {
        "code": "1",
        "version": "1.2",
        "status": 200,
        "description": "Generación de reportes en formato PDF.",
        "message": "Reportes PDF, esta activo y funciona correctamente.",
        "reports": ["Reporte General de stock", "Reporte General de stock reducido", "Reporte de Producto puntual",
                    "Reporte Desvio de stock", "Reporte de Inventario"]
    }






    json_output = json.dumps(data, indent=4)
    print(json_output)
    return json_output


@app.route('/generarReporte', methods=['POST'])
def generar_reporte():
    try:
        paramsJson = request.get_json()
        parametros = []
        temp = []
        parametros = {}

        for d in temp:
            parametros.update(d)
        if request.args.get('tipo') == "inventario":
            reporte_codigo = 10
        elif request.args.get('tipo') == "general-1":
            reporte_codigo = 1
        elif request.args.get('tipo') == "general-2":
            reporte_codigo = 2
        elif request.args.get('tipo') == "producto":
            reporte_codigo = 3
        elif request.args.get('tipo') == "desvio-stock":
            reporte_codigo = 4

        file_path = f"reporte_"+str(reporte_codigo)+".pdf"
        print("GeneradorReportes() ", request.get_json() )
        generador = TesterReportes()
        print("GeneradorReportes instanciado correctamente.")
        generador.generarReportes(file_path, parametros, reporte_codigo)
        print("GeneradorReportes culminó con éxito se envia el pdf para descargar.")
        return send_file(file_path)
    except Exception as e:
        #logging.error(f"Error generating report: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
   try:
       generador = TesterReportes()
       parametros = {"empresa": "2",
                     "conStockSn": True,
                     "titulo": "Titulo Reporte xxxxx",
                     "fechaDesde": "2022-01-01",
                     "fechaHasta": "2024-07-31",
                     "idCteTipo": "0",
                     "idDeposito": "6",
                     "idProducto": "0",
                     "idProductoDesde": "1",
                     "idProductoHasta": "100200",
                     "idRubro": "0",
                     "idRubrosGrupos": "0",
                     "idSubRubro": "0",
                     "orden": "0",
                     "tipoEstado": "0"}

       generador.main(parametros, 1)
       #app.run(debug=True, port=6001)
       print("Iniciando Aplicación GeneradorResportes ...")
   except Exception as e:
        msg = f"A ocurrido un error al intentar iniciar el servicio GeneradorResportes: {e}"
        print(msg)
        raise
