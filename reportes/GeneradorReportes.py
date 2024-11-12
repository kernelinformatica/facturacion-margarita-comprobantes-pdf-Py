from flask import Flask, request, g,  jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from decimal import Decimal
from conn.FacturacionConnection import FacturacionConnection as FacturacionConnnection
from datetime import datetime, timedelta
import logging
from PIL import Image
app = Flask(__name__)


#CORS(app)
# Configure logging
# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
# Initialize the database connection
parametros = {}

class GeneradorReportes(FacturacionConnnection):

    def __init__(self):
        print("-------------------------- INICIANDO PROCESO --------------------------------")
        super().__init__()
        self.datos = []
        self.datosUsu = []
        self.datosResuCer = []
        self.datosFichaCer = []
        self.maskCuenta = "0000000"
        self.maskNorComp = "0000-00000000"
        self.maskCosecha = "0000"
        print("Connection to MySQL ===================.")
        self.connFacturacion = FacturacionConnnection()

    def generarReportes(self, file_path, parameters, reporte):
        hoy = datetime.today().date()
        #logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',format='%(name)s - %(levelname)s - %(message)s')
        try:

            cursor = self.connFacturacion.conn.cursor()
            cursor.execute("SELECT prefijoEmpresa, nombre, descripcion, domicilio, cuit, telefono, situacionIva FROM Empresas WHERE idEmpresa ="+str(parameters["empresa"])+" ")
            empresa = cursor.fetchone()

        except Exception as e:
            logging.error(f"Error ejecutando query: {e}")
            print(f"Error ejecutando query: {e}")
        prefijoEmpresa = empresa[0]
        nombreEmpresa = empresa[1]
        descripcionEmpresa = empresa[2]
        domicilioEmpresa = empresa[3]
        cuitEmpresa = empresa[4]
        empresaSituacionIva = empresa[6]
        if reporte == 3:
            sql = "SELECT Productos.descripcion, Productos.codProducto, Rubros.descripcion AS rubro , SubRubros.descripcion AS subRubro from Productos, Rubros, SubRubros WHERE Productos.idSubRubros = SubRubros.idSubRubros and Rubros.idRubros = SubRubros.idRubros and Productos.idProductos = " + str(
                parameters["idProducto"]) + ""
            cursor.execute(sql)
            producto = cursor.fetchone()

        # Reporte 10 = Stock Inventario
        data = []

        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        page_number = 1
        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa,
                               cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number)
        # Reporte Stock General

        if reporte == 1:
            print(":: Generando Reporte stock General ::")

            self.encabezadoReporteStockGeneral(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            idProductoDesde = parameters.get('idProductoDesde', 0)
            if parameters["idProductoHasta"] == None:
                cursor.execute("SELECT MAX(idProductos) FROM Productos")
                result = cursor.fetchone()
                productoHasta = result[0]
            else:
                productoHasta = parameters.get('idProductoHasta', 0)

            cursor.callproc("s_buscaStockGral", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                idProductoDesde,
                productoHasta,
                parameters["idRubrosGrupos"],
                parameters["idRubro"],
                parameters["idSubRubro"],
                parameters["idDeposito"],
                parameters["tipoEstado"]))

            for result in cursor.stored_results():
                for row in result.fetchall():
                    page_number += 1
                    codProducto = row[0]
                    descripcionProducto = row[2][:28]
                    rubro = row[11][:10]
                    subRubro = row[12][:8]
                    fisicoImputado = row[5]
                    moneda = row[14]
                    precio = row[13]
                    precioCompra = row[15]
                    ingreso = row[3]
                    egreso = row[4]
                    ingresoVirtual = row[6]
                    egresoVirtual = row[7]
                    virtualImputado = row[8]
                    trazable = row[9]
                    stock = ingreso - egreso
                    stockVirtual = (ingresoVirtual - egresoVirtual - virtualImputado) + stock

                    data.append(
                        {"stock": "" + str(stock), "codProducto": "" + str(codProducto) + "",
                         "descripcion": "" + str(descripcionProducto) + "", "moneda": "" + str(moneda) + "",
                         "rubro": "" + str(rubro) + "", "subRubro": "" + str(subRubro) + "",
                         "fisicoImputado": "" + str(fisicoImputado) + "",
                         "stockFisico": "" + str(stock) + "", "ingresoVirtual": "" + str(ingresoVirtual) + "",
                         "egresoVirtual": "" + str(egresoVirtual) + "", "StockVirtual": "" + str(stockVirtual),
                         "trazable": "" + str(trazable), "ingreso": "" + str(ingreso), "egreso": "" + str(egreso)})

                # Table Data
                page_number = 1
                y = height - 180
                c.setFont("Helvetica", 7)
                y = height - 180  # Starting y-coordinate
                row_height = 15  # Height of each row
                available_height = height - 200
                total_fisico = 0
                for item in data:

                    if y < row_height:
                        page_number += 1
                        c.showPage()
                        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                               domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                               page_number)
                        y = height - 120

                    if parameters["conStockSn"] == True:
                        if Decimal(item["stock"]) != 0:
                            total_fisico += Decimal(item["stock"])
                            c.drawRightString(55, y, item["codProducto"])
                            c.drawString(60, y, item["descripcion"])
                            c.drawString(200, y, item["rubro"])
                            c.drawString(260, y, item["subRubro"])
                            c.drawRightString(340, y, item["ingreso"])
                            c.drawRightString(380, y, item["egreso"])
                            c.drawRightString(410, y, f"{Decimal(item['fisicoImputado']):,.2f}")
                            c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}")
                            c.drawRightString(490, y, f"{Decimal(item['ingresoVirtual']):,.2f}")
                            c.drawRightString(540, y, f"{Decimal(item['egresoVirtual']):,.2f}")
                            c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")
                            y -= row_height

                    else:
                        total_fisico += Decimal(item["stock"])
                        c.drawRightString(55, y, item["codProducto"])
                        c.drawString(60, y, item["descripcion"])
                        c.drawString(200, y, item["rubro"])
                        c.drawString(260, y, item["subRubro"])
                        c.drawRightString(340, y, item["ingreso"])
                        c.drawRightString(380, y, item["egreso"])
                        c.drawRightString(410, y, f"{Decimal(item['fisicoImputado']):,.2f}")
                        c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}")
                        c.drawRightString(490, y, f"{Decimal(item['ingresoVirtual']):,.2f}")
                        c.drawRightString(540, y, f"{Decimal(item['egresoVirtual']):,.2f}")
                        c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")
                        y -= row_height

                y -= 20

                c.setFont("Helvetica-Bold", 9)
                c.drawRightString(580, y, f"Total Fisico: {total_fisico}")
                y -= row_height

        if reporte == 2:
            print(":: Generando Reporte stock General reducido ::")

            self.encabezadoReporteStockGeneral_2(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            idProductoDesde = parameters.get('idProductoDesde', 0)
            if parameters["idProductoHasta"] == None:
                cursor.execute("SELECT MAX(idProductos) FROM Productos")
                result = cursor.fetchone()
                productoHasta = result[0]
            else:
                productoHasta = parameters.get('idProductoHasta', 0)

            cursor.callproc("s_buscaStockGral", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                idProductoDesde,
                productoHasta,
                parameters["idRubrosGrupos"],
                parameters["idRubro"],
                parameters["idSubRubro"],
                parameters["idDeposito"],
                parameters["tipoEstado"]))

            for result in cursor.stored_results():
                for row in result.fetchall():
                    page_number += 1
                    codProducto = row[0]
                    descripcionProducto = row[2][:28]
                    rubro = row[11][:10]
                    subRubro = row[12][:8]
                    fisicoImputado = row[5]
                    grupo = row[16]
                    moneda = row[14]
                    precio = row[13]
                    precioCompra = row[15]
                    ingreso = row[3]
                    egreso = row[4]
                    ingresoVirtual = row[6]
                    egresoVirtual = row[7]
                    virtualImputado = row[8]
                    trazable = row[9]
                    stock = ingreso - egreso
                    stockVirtual = (ingresoVirtual - egresoVirtual - virtualImputado) + stock

                    data.append(
                        {"stock": "" + str(stock), "codProducto": "" + str(codProducto) + "",
                         "descripcion": "" + str(descripcionProducto) + "", "moneda": "" + str(moneda) + "",
                         "grupo": "" + str(grupo), "rubro": "" + str(rubro) + "", "subRubro": "" + str(subRubro) + "",
                         "fisicoImputado": "" + str(fisicoImputado) + "",
                         "stockFisico": "" + str(stock) + "", "ingresoVirtual": "" + str(ingresoVirtual) + "",
                         "egresoVirtual": "" + str(egresoVirtual) + "", "StockVirtual": "" + str(stockVirtual),
                         "trazable": "" + str(trazable), "ingreso": "" + str(ingreso), "egreso": "" + str(egreso)})

                # Table Data
                page_number = 1
                y = height - 180
                c.setFont("Helvetica", 7)
                y = height - 180  # Starting y-coordinate
                row_height = 15  # Height of each row
                available_height = height - 200
                total_fisico = 0
                for item in data:

                    if y < row_height:
                        page_number += 1
                        c.showPage()
                        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                               domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                               page_number)
                        y = height - 120  # Reset y-coordinate after drawing the header

                    if parameters["conStockSn"] == True:
                        if Decimal(item["stock"]) != 0:
                            total_fisico += Decimal(item["stock"])
                            c.drawRightString(55, y, item["codProducto"])
                            c.drawString(60, y, item["descripcion"])
                            c.drawString(200, y, item["grupo"])
                            c.drawRightString(310, y, item["ingreso"])
                            c.drawRightString(380, y, item["egreso"])
                            c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}")
                            c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")
                            y -= row_height
                    else:
                        total_fisico += Decimal(item["stock"])
                        c.drawRightString(55, y, item["codProducto"])
                        c.drawString(60, y, item["descripcion"])
                        c.drawString(200, y, item["grupo"])
                        c.drawRightString(310, y, item["ingreso"])
                        c.drawRightString(380, y, item["egreso"])
                        c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}")
                        c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")
                        y -= row_height

                y -= 20
                c.setFont("Helvetica-Bold", 9)
                c.drawRightString(580, y, f"Total Fisico: {total_fisico}")

        if reporte == 3:
            print(":: Generando Reporte stock por Producto ::")

            self.encabezadoReporteStockProducto(c, height, parameters, producto)
            cursor.callproc("s_buscaStock", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                parameters["idProducto"],
                parameters["idDeposito"],
                parameters["idCteTipo"],
                parameters["tipoEstado"], 0))
            totalStockVirtual = 0
            totalStock = 0
            for result in cursor.stored_results():
                for row in result.fetchall():
                    page_number += 1
                    comprobanteAbrev = row[0]
                    numero = row[1]
                    fecha = row[2]
                    idProducto = row[3]
                    codProducto = row[4]
                    ingreso = row[5]
                    egreso = row[6]
                    pendiente = row[7]
                    if row[18] is None:
                        precioCompra = Decimal(0)
                    else:
                        precioCompra = row[18]

                    rubro = row[10]
                    subrRubro = row[11]
                    idFactCab = row[12]
                    pendiente = 0
                    # calculo stock y virtual
                    if comprobanteAbrev == "CST":
                        print("Corte de Stock --> " + str(ingreso))
                        stock = ingreso
                        stockTotal = (stock)
                        totalStock = stockTotal
                        virtual = (ingreso - egreso) + pendiente
                        totalStockVirtual = virtual
                    else:
                        stock = ingreso - egreso
                        stockTotal = (stock)
                        totalStock += stockTotal
                        virtual = (ingreso - egreso) + pendiente
                        totalStockVirtual += virtual

                    data.append({"precioCompra": "" + str(precioCompra)
                                                 + "", "idFactCab": "" + str(idFactCab)
                                                                    + "", "ingreso": "" + str(ingreso)
                                                                                     + "", "egreso": "" + str(egreso)
                                                                                                     + "",
                                 "comprobante": "" + str(comprobanteAbrev)
                                                + "", "numero": ""
                                                                + str(numero) + "", "fecha": ""
                                                                                             + str(fecha) + "",
                                 "codProducto": ""
                                                + str(codProducto)
                                                + "", "descripcion": "" + str("descripcion del prudcto")
                                                                     + "", "virtual": "" + str(totalStockVirtual)
                                                                                      + "", "moneda": "" + str("0")
                                                                                                      + "",
                                 "precioCompra": "" + str(precioCompra)
                                                 + "", "stock": "" + str(totalStock)
                                                                + "", "rubro": "" + str(rubro)
                                                                               + "", "subRubro": "" + str(subrRubro)
                                                                                                 + "",
                                 "pendiente": "" + str(pendiente)})

            # end encabezado

            # Table Data
            page_number = 1
            y = height - 180
            c.setFont("Helvetica", 8)
            y = height - 180  # Starting y-coordinate
            row_height = 15  # Height of each row
            available_height = height - 200
            total_fisico = 0
            total_stock_virtual = 0

            for item in data:
                if y < row_height:
                    page_number += 1
                    c.showPage()
                    self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                           domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                           page_number)
                    self.encabezadoReporteStockProducto(c, height, parameters, producto)
                    y = height - 180  # Reset y-coordinate after drawing the header
                if parameters["conStockSn"] == True:
                    if Decimal(item["virtual"]) != 0:
                        total_fisico += Decimal(item["virtual"])
                        total_stock_virtual += Decimal(item["stock"])
                        c.drawString(20, y, item["comprobante"])
                        c.drawRightString(90, y, item["numero"])
                        c.drawString(100, y, item["fecha"])

                        c.drawRightString(200, y, str(item["ingreso"]))
                        c.drawRightString(280, y, item["egreso"])
                        c.drawRightString(360, y, str(item["precioCompra"]))
                        c.drawRightString(440, y, str(item["stock"]))
                        c.drawRightString(510, y, str(item["pendiente"]))
                        c.drawRightString(580, y, str(item["virtual"]))
                        y -= row_height


                else:
                    total_fisico += Decimal(item["virtual"])
                    total_stock_virtual += Decimal(item["stock"])
                    c.drawString(20, y, item["comprobante"])
                    c.drawRightString(90, y, item["numero"])
                    c.drawString(100, y, item["fecha"])

                    c.drawRightString(200, y, str(item["ingreso"]))
                    c.drawRightString(280, y, item["egreso"])
                    c.drawRightString(360, y, str(item["precioCompra"]))
                    c.drawRightString(440, y, str(item["stock"]))
                    c.drawRightString(510, y, str(item["pendiente"]))
                    c.drawRightString(580, y, str(item["virtual"]))
                    y -= row_height
            y -= 20
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(580, y, f"Total Fisico: {total_fisico}")
            y -= 20
            c.drawRightString(580, y, f"Total Virtual: {total_stock_virtual}")

        if reporte == 4:
            print(":: Generando Reporte Desvio de Stock ::")
            self.encabezadoReporteStockGeneralDesvio(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            idProductoDesde = parameters.get('idProductoDesde', 0)
            if parameters["idProductoHasta"] == None:
                cursor.execute("SELECT MAX(idProductos) FROM Productos")
                result = cursor.fetchone()
                productoHasta = result[0]
            else:
                productoHasta = parameters.get('idProductoHasta', 0)
            cursor.callproc("s_buscaStockGral", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                idProductoDesde,
                productoHasta,
                parameters["idRubrosGrupos"],
                parameters["idRubro"],
                parameters["idSubRubro"],
                parameters["idDeposito"],
                parameters["tipoEstado"]))

            for result in cursor.stored_results():
                for row in result.fetchall():

                    totalStock = 0
                    egresoTotal = 0
                    totalStockVirtual = 0
                    page_number += 1
                    idProducto = Decimal(row[1])
                    cursor.callproc("s_buscaStock", (
                        parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                        idProducto,
                        parameters["idDeposito"],
                        0,
                        parameters["tipoEstado"], 0))

                    codProducto = row[0]
                    descripcionProducto = row[2][:28]
                    rubro = row[11][:10]
                    subRubro = row[12][:8]
                    fisicoImputado = row[5]
                    grupo = row[16]
                    moneda = row[14]
                    precio = row[13]
                    precioCompra = row[15]
                    ingreso = row[3]
                    egreso = row[4]
                    ingresoVirtual = row[6]
                    egresoVirtual = row[7]
                    virtualImputado = row[8]
                    trazable = row[9]
                    #stock = ingreso - egreso
                    #  stockVirtual = (ingresoVirtual - egresoVirtual - virtualImputado) + stock
                    for result2 in cursor.stored_results():
                        for row2 in result2.fetchall():
                            comprobanteAbrev = row2[0]
                            codProducto = row2[4]
                            pendiente = row2[7]
                            ingreso = row2[5]
                            egreso = row2[6]
                            rubro = row2[10]
                            pendiente = 0
                            if comprobanteAbrev != "CST":
                                stock = ingreso - egreso
                                stockTotal = (stock)
                                egresoTotal = (egreso)
                                totalStock += stockTotal
                                egresoTotal += egresoTotal
                                virtual = (ingreso - egreso) + pendiente
                                totalStockVirtual += virtual
                                stockVirtual = (ingresoVirtual - egresoVirtual - virtualImputado) + stock

                    data.append(
                        {"stock": "" + str(stock), "codProducto": "" + str(codProducto) + "",
                         "descripcion": "" + str(descripcionProducto) + "", "moneda": "" + str(moneda) + "",
                         "grupo": "" + str(grupo), "rubro": "" + str(rubro) + "", "subRubro": "" + str(subRubro) + "",
                         "fisicoImputado": "" + str(fisicoImputado) + "",
                         "stockFisico": "" + str(totalStock) + "", "ingresoVirtual": "" + str(ingresoVirtual) + "",
                         "egresoVirtual": "" + str(egresoVirtual) + "", "StockVirtual": "" + str(stockVirtual),
                         "trazable": "" + str(trazable), "ingreso": "" + str(ingreso), "egreso": "" + str(egreso)})

                # Table Data
                page_number = 1
                y = height - 180
                c.setFont("Helvetica", 7)
                y = height - 180  # Starting y-coordinate
                row_height = 15  # Height of each row
                available_height = height - 200
                total_fisico = 0
                for item in data:
                    codProducto = item["codProducto"]
                    sql = "SELECT idProductos, Productos.descripcion, Productos.codProducto FROM Productos WHERE Productos.codProducto = %s"
                    cursor.execute(sql, (codProducto,))
                    producto = cursor.fetchone()
                    if producto:
                        idProducto = producto[0]
                    else:
                        idProducto = 0

                    if y < row_height:
                        page_number += 1
                        c.showPage()
                        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                               domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                               page_number)
                        y = height - 120  # Reset y-coordinate after drawing the header

                    parameters["conStockSn"] = True
                    if parameters["conStockSn"] == True:
                        # Buso el movimiento de corte de stock si es que tiene
                        cursor.execute("SELECT * FROM Produmo  WHERE idCteTipo = 89 AND idProductos = " + str(
                            idProducto) + " and idDepositos = " + str(parameters["idDeposito"]) + "")
                        cst = cursor.fetchone()
                        if cst is None:
                            cstIngreso = 0
                        else:
                            cstIngreso = Decimal(cst[5]) if cst is not None else 0
                        stockFisico = item["stockFisico"]
                        if (Decimal(cstIngreso) != Decimal(stockFisico)) and cst is not None:

                            if Decimal(item["ingreso"]) >= 0:
                                total_fisico += Decimal(item["stock"])
                                c.drawRightString(55, y, codProducto)
                                c.drawString(60, y, item["descripcion"])
                                c.drawString(200, y, item["grupo"])
                                #c.drawRightString(330, y, item["ingreso"])
                                #c.drawRightString(380, y, item["egreso"])
                                c.drawRightString(580, y, f"{Decimal(stockFisico) :,.2f}")

                                # agrego movimiento de corte de stock para comparar
                                y -= row_height - 5
                                if cst is not None:
                                    cstCodProducto = codProducto
                                    cstDescripcionProducto = "Corte de Stock"
                                    cstGrupo = item["grupo"]

                                    cstEgreso = 0
                                    stock = cstIngreso - cstEgreso

                                    c.drawRightString(55, y, codProducto)
                                    c.drawString(60, y, cstDescripcionProducto)
                                    c.drawString(200, y, cstGrupo)
                                    #c.drawRightString(330, y, str(Decimal(cstIngreso)))
                                    #c.drawRightString(380, y, str(Decimal(cstEgreso)))
                                    c.drawRightString(580, y, str(Decimal(stock)))

                                    y -= row_height

                                y -= row_height
                    else:
                        total_fisico += Decimal(item["stock"])
                        c.drawRightString(55, y, item["codProducto"])
                        c.drawString(60, y, item["descripcion"])
                        c.drawString(200, y, item["grupo"])
                        #c.drawRightString(310, y, item["ingreso"])
                        #c.drawRightString(380, y, item["egreso"])
                        c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}")
                        c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")
                        y -= row_height

                y -= 10

        # Reporte Inventario
        if reporte == 10:
            print(":: Generando Reporte de Inventario ::")
            self.encabezadoReporteInventario(c, height, parameters)
            idProductoDesde = parameters.get('idProductoDesde', 0)
            if parameters["idProductoHasta"] == None:
                cursor.execute("SELECT MAX(idProductos) FROM Productos")
                result = cursor.fetchone()
                productoHasta = result[0]
            else:
                productoHasta = parameters.get('idProductoHasta', 0)

            cursor.callproc("s_buscaStockGral", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                idProductoDesde,
                productoHasta, parameters["idRubrosGrupos"], parameters["idRubro"],
                parameters["idSubRubro"], parameters["idDeposito"],
                parameters["tipoEstado"]))

            for result in cursor.stored_results():
                for row in result.fetchall():
                    page_number += 1
                    codProducto = row[0]
                    descripcionProducto = row[2]
                    grupo = row[16]
                    rubro = row[11]
                    subRubro = row[12]
                    fisicoImputado = row[5]
                    moneda = row[14]
                    precio = row[13]
                    precioCompra = row[15]
                    ingreso = row[3]
                    egreso = row[4]
                    stock = ingreso - egreso
                    ingresoVirtual = row[6]
                    egresoVirtual = row[7]
                    virtualImputado = row[8]
                    stockVirtual = egresoVirtual - ingresoVirtual - virtualImputado + stock

                    if moneda == "u$s":
                        totalValoracionUss = precioCompra * stock
                    else:
                        totalValoracionUss = 0

                    if moneda == "$AR":
                        totalValoracionPes = precioCompra * stock
                    else:
                        totalValoracionPes = 0

                    data.append(
                        {"codProducto": "" + str(codProducto) + "", "descripcion": "" + str(descripcionProducto) + "",
                         "rubro": "" + str(rubro) + "", "fisico": "" + str(stock) + "",
                         "moneda": "" + str(moneda) + "", "precioCompra": "" + str(precioCompra) + "",
                         "grupo": "" + str(grupo) + "",
                         "stock": "" + str(stock) + ""})

            #end encabezado

            # Table Data
            page_number = 1
            y = height - 180
            c.setFont("Helvetica", 8)
            y = height - 180  # Starting y-coordinate
            row_height = 15  # Height of each row
            available_height = height - 200
            total_fisico = 0
            total_val_dol = 0
            total_val_pes = 0
            for item in data:
                if y < row_height:
                    page_number += 1
                    c.showPage()
                    self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                           domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                           page_number)
                    self.encabezadoReporteInventario(c, height, parameters)
                    y = height - 180  # Reset y-coordinate after drawing the header

                if parameters["conStockSn"] == True:
                    if Decimal(item["fisico"]) != 0:
                        total_fisico += Decimal(item["fisico"])
                        #total_val_dol += Decimal(item["precioCompra"]) * Decimal(item["stock"]) if item[ "moneda"] == "u$s" else 0
                        #total_val_pes += Decimal(item["precioCompra"]) * Decimal(item["stock"]) if item["moneda"] == "$AR" else 0
                        c.drawRightString(60, y, item["codProducto"])
                        c.drawString(80, y, item["descripcion"])
                        c.drawString(300, y, item["grupo"])
                        c.drawRightString(570, y, str(item["fisico"]))
                        #c.drawRightString(350, y, item["moneda"])
                        #c.drawRightString(400, y,f"{Decimal(item['precioCompra']):,.2f}" if item["moneda"] == "u$s" else "0.00")
                        #c.drawRightString(450, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[                                                                                                              "moneda"] == "u$s" else "0.00")
                        #c.drawRightString(500, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item["moneda"] == "$AR" else "0.00")
                        #c.drawRightString(570, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[ "moneda"] == "$AR" else "0.00")
                        y -= row_height
                else:
                    total_fisico += Decimal(item["fisico"])
                    # total_val_dol += Decimal(item["precioCompra"]) * Decimal(item["stock"]) if item[ "moneda"] == "u$s" else 0
                    # total_val_pes += Decimal(item["precioCompra"]) * Decimal(item["stock"]) if item["moneda"] == "$AR" else 0
                    c.drawRightString(60, y, item["codProducto"])
                    c.drawString(80, y, item["descripcion"])
                    c.drawString(300, y, item["grupo"])
                    c.drawRightString(570, y, str(item["fisico"]))
                    # c.drawRightString(350, y, item["moneda"])
                    # c.drawRightString(400, y,f"{Decimal(item['precioCompra']):,.2f}" if item["moneda"] == "u$s" else "0.00")
                    # c.drawRightString(450, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[                                                                                                              "moneda"] == "u$s" else "0.00")
                    # c.drawRightString(500, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item["moneda"] == "$AR" else "0.00")
                    # c.drawRightString(570, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[ "moneda"] == "$AR" else "0.00")
                    y -= row_height
            y -= 20
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(570, y, f"Total Fisico: {total_fisico}")
            #c.drawRightString(450, y, f"Total Val Dol: {total_val_dol:,.2f}")
            #c.drawRightString(570, y, f"Total Val Pes: {total_val_pes:,.2f}")

        c.save()
        #cursor.close()

    # Example usage
    def encabezadoReporte(self, c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa,
                          cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number):
        # Title Right
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(width - 30, height - 50, parameters['titulo'])
        c.setFont("Helvetica", 8)
        c.drawRightString(width - 30, height - 65, "Emitido el: " + str(hoy))
        c.drawRightString(width - 30, height - 80, f"Página: {page_number}")
        c.drawRightString(width - 30, height - 95, f"Corte de Stock: " + str(parameters["fechaHasta"]))
        # Title Left
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, height - 50, str(nombreEmpresa))
        c.setFont("Helvetica", 10)
        c.drawString(100, height - 60, str(descripcionEmpresa))
        c.setFont("Helvetica", 8)
        c.drawString(100, height - 70, "Domicilio: " + str(domicilioEmpresa))
        c.drawString(100, height - 80, "Cuit: " + str(cuitEmpresa) + ", " + str(empresaSituacionIva))

        # Logo
        logo_path = "img/" + str(prefijoEmpresa) + ".png"
        try:
             c.drawImage(logo_path, 15, height - 95, width=70, height=70)
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 103, 580, height - 103)

        # Reset font to regular after header
        c.setFont("Helvetica", 8)

    def encabezadoReporteStockGeneral(self, c, height, parameters):

        idDeposito = parameters.get('idDeposito', 0)
        idProducto = parameters.get('idProducto', 0)
        idRubro = parameters.get('idRubro', 0)
        idSubRubro = parameters.get('idSubRubro', 0)
        idProductoDesde = parameters.get('idProductoDesde', 0)
        idProductoHasta = parameters.get('idProductoHasta', 0)
        cursor = self.conn.cursor()
        sql = "SELECT descripcion FROM Depositos WHERE idDepositos = " + str(idDeposito)
        cursor.execute(sql)
        deposito = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawRightString(580, height - 115, f"Prod Desde: {idProductoDesde}")
        c.drawRightString(580, height - 125, f"Prod Hasta: {idProductoHasta}")
        c.drawRightString(580, height - 135, f"Deposito: {deposito[0]}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 140, 580, height - 140)

        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(55, height - 155, "Codigo")
        c.drawString(60, height - 155, "Descripcion")
        c.drawString(220, height - 155, "Rubro")
        c.drawString(260, height - 155, "Sub Rubro")
        c.drawRightString(340, height - 155, "Ingr")
        c.drawRightString(380, height - 155, "Egre")
        c.drawRightString(410, height - 155, "Fis Imp")
        c.drawRightString(460, height - 155, "Fisico")
        c.drawRightString(490, height - 155, "Ing Virt")
        c.drawRightString(540, height - 155, "Eg Virt")
        c.drawRightString(580, height - 155, "Stock V")
        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 165, 580, height - 165)
        c.setFont("Helvetica", 8)

    def encabezadoReporteStockGeneral_2(self, c, height, parameters):

        dDeposito = parameters.get('idDeposito', 0)
        idProducto = parameters.get('idProducto', 0)
        idRubro = parameters.get('idRubro', 0)
        idSubRubro = parameters.get('idSubRubro', 0)
        idProductoDesde = parameters.get('idProductoDesde', 0)
        idProductoHasta = parameters.get('idProductoHasta', 0)
        cursor = self.conn.cursor()
        sql = "SELECT descripcion FROM Depositos WHERE idDepositos = " + str(idDeposito)
        cursor.execute(sql)
        deposito = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawRightString(580, height - 115, f"Prod Desde: {idProductoDesde}")
        c.drawRightString(580, height - 125, f"Prod Hasta: {idProductoHasta}")
        c.drawRightString(580, height - 135, f"Deposito: {deposito[0]}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 140, 580, height - 140)

        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(55, height - 155, "Codigo")
        c.drawString(60, height - 155, "Descripcion")
        c.drawString(200, height - 155, "Grupo")
        c.drawRightString(310, height - 155, "Ingreso")
        c.drawRightString(380, height - 155, "Egreso")
        c.drawRightString(460, height - 155, "Fisico")
        c.drawRightString(580, height - 155, "Stock Virtual")
        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 165, 580, height - 165)
        c.setFont("Helvetica", 8)

    def encabezadoReporteStockProducto(self, c, height, parameters, producto):

        descripcionProducto = producto[0]
        codigoProducto = producto[1]
        rubro = producto[2]
        subRubro = producto[3]
        # Encabezado 2
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20, height - 120, f"" + str(descripcionProducto))
        c.setFont("Helvetica", 8)
        c.drawRightString(580, height - 120, f"RUBRO: " + str(rubro))
        c.drawRightString(580, height - 133, f"SUB RUBRO: " + str(subRubro))
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 133, f"CODIGO: " + str(codigoProducto))

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 140, 580, height - 140)

        # Table Header
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(50, height - 155, "Codigo")
        c.drawString(60, height - 155, "Numero")
        c.drawString(100, height - 155, "Fecha")

        c.drawRightString(200, height - 155, "Ingreso")
        c.drawRightString(280, height - 155, "Egreso")
        c.drawRightString(360, height - 155, "PreComp")
        c.drawRightString(440, height - 155, "Stock")
        c.drawRightString(510, height - 155, "Pendiente")
        c.drawRightString(580, height - 155, "Virtual")
        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 165, 580, height - 165)
        c.setFont("Helvetica", 8)

    def encabezadoReporteInventario(self, c, height, parameters):
        idDeposito = parameters.get('idDeposito', 0)
        idProducto = parameters.get('idProducto', 0)
        idRubro = parameters.get('idRubro', 0)
        idSubRubro = parameters.get('idSubRubro', 0)
        idProductoDesde = parameters.get('idProductoDesde', 0)
        idProductoHasta = parameters.get('idProductoHasta', 0)
        cursor = self.conn.cursor()
        sql = "SELECT descripcion FROM Depositos WHERE idDepositos = " + str(idDeposito)
        cursor.execute(sql)
        deposito = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawString(20, height - 135, f"Deposito: {deposito[0]}")
        c.drawRightString(575, height - 115, f"Prod Desde: {idProductoDesde}")
        c.drawRightString(575, height - 125, f"Prod Hasta: {idProductoHasta}")
        #c.drawString(500, height - 115, f"Rubro: {datos[4]}")
        #c.drawString(500, height - 125, f"Sub Rubro: {datos[6]}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 140, 580, height - 140)

        # Table Header
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(60, height - 155, "Codigo")
        c.drawString(80, height - 155, "Descripcion")
        c.drawString(300, height - 155, "Grupo")
        c.drawRightString(570, height - 155, "Fisico")
        #c.drawRightString(350, height - 155, "Mon")
        #c.drawRightString(400, height - 155, "PC Dol")
        #c.drawRightString(450, height - 155, "Val Dol")
        #c.drawRightString(500, height - 155, "PC Pes")
        #c.drawRightString(570, height - 155, "Val Pes")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 165, 580, height - 165)
        c.setFont("Helvetica", 8)

    def encabezadoReporteStockGeneralDesvio(self, c, height, parameters):

        idDeposito = parameters.get('idDeposito', 0)
        idProducto = parameters.get('idProducto', 0)
        idRubro = parameters.get('idRubro', 0)
        idSubRubro = parameters.get('idSubRubro', 0)
        idProductoDesde = parameters.get('idProductoDesde', 0)
        idProductoHasta = parameters.get('idProductoHasta', 0)
        cursor = self.conn.cursor()
        sql = "SELECT descripcion FROM Depositos WHERE idDepositos = " + str(idDeposito)
        cursor.execute(sql)
        deposito = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawRightString(580, height - 115, f"Prod Desde: {idProductoDesde}")
        c.drawRightString(580, height - 125, f"Prod Hasta: {idProductoHasta}")
        c.drawRightString(580, height - 135, f"Deposito: {deposito[0]}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 140, 580, height - 140)

        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(55, height - 155, "Codigo")
        c.drawString(60, height - 155, "Descripcion")
        c.drawString(200, height - 155, "Grupo")
        #c.drawRightString(330, height - 155, "Ingreso")
        #c.drawRightString(380, height - 155, "Egreso")
        c.drawRightString(580, height - 155, "Stock")
        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 165, 580, height - 165)
        c.setFont("Helvetica", 8)

    def main(self, parameters, reporteCodigo):
        self.generarReportes("reporte_" + str(reporteCodigo) + ".pdf", parameters, reporteCodigo)


@app.route('/dummy', methods=['GET'])
def dummy():
    import json
    data = {
        "code": "1",
        "version": "1.3",
        "status": 200,
        "description": "Generación de reportes en formato PDF.",
        "name": "Reportes PDF",
        "message": "Reportes PDF, esta activo y funciona correctamente.",
        "reports": ["Reporte General de stock", "Reporte General de stock reducido", "Reporte de Producto puntual",
                    "Reporte Desvio de stock", "Reporte de Inventario"]
    }






    json_output = json.dumps(data, indent=4)
    return json_output



@app.before_request
def before_request_func():
    # Código que se ejecuta antes de procesar cada solicitud
    #generar_reporte()
    print("Antes de procesar la solicitud")




@app.route('/generarReportePdf', methods=['POST'])
def generar_reporte():
    paramsJson = request.get_json()
    print("PARAMETROS: " + str(paramsJson))
    logging.error(f"Parametros query: {paramsJson}")
    for key, value in paramsJson.items():
        #(f"{key}: {value}")
        parametros.update({key: value})

    try:

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
        generador = GeneradorReportes()
        print("GeneradorReportes instanciado correctamente.")
        generador.connFacturacion = FacturacionConnnection()
        generador.generarReportes(file_path, parametros, reporte_codigo)
        print("GeneradorReportes culminó con éxito se envia el pdf para descargar.")
        return send_file(file_path)
    except Exception as e:
        logging.error(f"Error generando el reporte: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
   try:
       #generador = GeneradorReportes()
       parametros = {"empresa": "2",
                     "conStockSn": True,
                     "titulo": "Titulo Reporte xxxxx",
                     "fechaDesde": "2022-01-01",
                     "fechaHasta": "2024-07-31",
                     "idCteTipo": "0",
                     "idDeposito": "10",
                     "idProducto": "0",
                     "idProductoDesde": "200",
                     "idProductoHasta": "200",
                     "idRubro": "0",
                     "idRubrosGrupos": "0",
                     "idSubRubro": "0",
                     "orden": "0",
                     "tipoEstado": "0"}

       #generador.main(parametros, 4)
       app.run(debug=True, port=6003)

   except Exception as e:
        msg = f"A ocurrido un error al intentar iniciar el servicio GeneradorResportes: {e}"
        logging.error(f"Parametros query: {msg}")
        raise
