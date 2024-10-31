from flask import Flask, request, jsonify, send_file
#from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from decimal import Decimal
from conn.FacturacionConnection import FacturacionConnection as FacturacionConnnection
from datetime import datetime, timedelta

app = Flask(__name__)
#CORS(app)
class GeneradorReportes(FacturacionConnnection ):
    def __init__(self):
        super().__init__()
        self.datos = []
        self.datosUsu = []
        self.datosResuCer = []
        self.datosFichaCer = []
        #self.hoy = datetime.now()
        self.maskCuenta = "0000000"
        self.maskNorComp = "0000-00000000"
        self.maskCosecha = "0000"
        self.connFacturacion = FacturacionConnnection()

    def generarReportes(self, file_path, parameters, reporte):
        print("::: Iniciando generacion de reportes ("+str(reporte)+")...")

        hoy = datetime.today().date()
        cursor = self.conn.cursor()
        #traigo datos de la empresa

        cursor.execute("SELECT prefijoEmpresa, nombre, descripcion, domicilio, cuit, telefono, situacionIva FROM Empresas WHERE idEmpresa = %s", (parameters["empresa"],))
        empresa = cursor.fetchone()
        prefijoEmpresa = empresa[0]
        nombreEmpresa = empresa[1]
        descripcionEmpresa = empresa[2]
        domicilioEmpresa = empresa[3]
        cuitEmpresa = empresa[4]
        empresaSituacionIva = empresa[6]
        if reporte == 3 :
            sql = "SELECT Productos.descripcion, Productos.codProducto, Rubros.descripcion AS rubro , SubRubros.descripcion AS subRubro from Productos, Rubros, SubRubros WHERE Productos.idSubRubros = SubRubros.idSubRubros and Rubros.idRubros = SubRubros.idRubros and Productos.idProductos = "+str(parameters["idProducto"])+""
            cursor.execute(sql)
            producto = cursor.fetchone()



        # Reporte 10 = Stock Inventario
        data = []

        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        page_number = 1
        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number)
        # Reporte Stock General


        if reporte == 1:
            print(":: Generando Reporte stock General ::")
            self.encabezadoReporteStockGeneral(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            cursor.callproc("s_buscaStockGral", (
                    parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                    parameters["idProductoDesde"],
                    parameters["idProductoHasta"], 0, parameters["idRubro"], parameters["idSubRubro"],
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
                    stockVirtual = (ingresoVirtual-egresoVirtual - virtualImputado) + stock

                    data.append(
                        {"stock": "" + str(stock), "codProducto": "" + str(codProducto) + "", "descripcion": "" + str(descripcionProducto) + "", "moneda": "" + str(moneda) + "",
                         "rubro": "" + str(rubro) + "",  "subRubro": "" + str(subRubro) + "","fisicoImputado": "" + str(fisicoImputado) + "",
                         "stockFisico": "" + str(stock) + "", "ingresoVirtual": "" + str(ingresoVirtual) + "",
                         "egresoVirtual": "" + str(egresoVirtual) + "", "StockVirtual": "" + str(stockVirtual), "trazable": "" + str(trazable), "ingreso": "" + str(ingreso), "egreso": "" + str(egreso) })

                # Table Data
                page_number = 1
                y = height - 180
                c.setFont("Helvetica", 7)
                y = height - 180  # Starting y-coordinate
                row_height = 15  # Height of each row
                available_height = height - 200
                for item in data:

                    if y < row_height:
                       page_number += 1
                       c.showPage()
                       self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number)
                       y = height - 120
                    c.drawRightString(55, y, item["codProducto"])
                    c.drawString(60, y, item["descripcion"])
                    c.drawString(200, y, item["rubro"])
                    c.drawString(260, y, item["subRubro"])
                    c.drawRightString(340, y, item["ingreso"])
                    c.drawRightString(380, y, item["egreso"])
                    c.drawRightString(410, y,  f"{Decimal(item['fisicoImputado']):,.2f}")
                    c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}"  )
                    c.drawRightString(490, y, f"{Decimal(item['ingresoVirtual']):,.2f}" )
                    c.drawRightString(540, y, f"{Decimal(item['egresoVirtual']):,.2f}" )
                    c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")




                    y -= row_height
                y -= 20

        if reporte == 2:
            print(":: Generando Reporte stock General 2 ::")
            self.encabezadoReporteStockGeneral_2(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            cursor.callproc("s_buscaStockGral", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                parameters["idProductoDesde"],
                parameters["idProductoHasta"], 0, parameters["idRubro"], parameters["idSubRubro"],
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
                         "grupo": "" + str(grupo) ,"rubro": "" + str(rubro) + "", "subRubro": "" + str(subRubro) + "",
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
                for item in data:

                    if y < row_height:
                        page_number += 1
                        c.showPage()
                        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                               domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                               page_number)
                        y = height - 120
                    c.drawRightString(55, y, item["codProducto"])
                    c.drawString(60, y, item["descripcion"])
                    c.drawString(200, y, item["grupo"])
                    c.drawRightString(310, y, item["ingreso"])
                    c.drawRightString(380, y, item["egreso"])
                    c.drawRightString(460, y, f"{Decimal(item['stock']) :,.2f}")
                    c.drawRightString(580, y, f"{Decimal(item['StockVirtual']):,.2f}")

                    


                    y -= row_height
                y -= 20




        if reporte == 3:
            print(":: Generando Reporte stock por Producto ::")
            self.encabezadoReporteStockProducto(c, height, parameters, producto)
            cursor.callproc("s_buscaStock", (
                parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"],
                parameters["idProducto"],
                parameters["idDeposito"],
                parameters["idCteTipo"],
                parameters["tipoEstado"], 0))
            totalStockVirtual =0
            totalStock =0
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
                    pendiente =0
                    # calculo stock y virtual
                    if comprobanteAbrev == "CST":
                        print("Corte de Stock --> "+str(ingreso))
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



                    data.append({ "precioCompra": "" + str(precioCompra)
                                        + "","idFactCab": "" + str(idFactCab)
                                        + "","ingreso": "" + str(ingreso)
                                        + "","egreso": "" + str(egreso)
                                        + "","comprobante": "" + str(comprobanteAbrev)
                                        + "","numero": ""
                                        + str(numero) + "", "fecha": ""
                                        + str(fecha) + "","codProducto": ""
                                        + str(codProducto)
                                        + "", "descripcion": ""+ str("descripcion del prudcto")
                                        + "", "virtual": "" + str(totalStockVirtual)
                                        + "", "moneda": ""+ str("0")
                                        + "", "precioCompra": ""+ str(precioCompra)
                                        + "", "stock": "" + str(totalStock)
                                        + "", "rubro": "" + str(rubro)
                                        + "", "subRubro": ""+ str(subrRubro)
                                        + "", "pendiente": ""+ str(pendiente)})

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
            y-= 20
            c.drawRightString(580, y, f"Total Virtual: {total_stock_virtual}")





        # Reporte Stock General
        if reporte == 10:
            print(":: Generando Reporte de Inventario ::")
            self.encabezadoReporteInventario(c, height,  parameters)
            cursor.callproc("s_buscaStockGral", (
            parameters["empresa"], parameters["fechaDesde"], parameters["fechaHasta"], parameters["idProductoDesde"],
            parameters["idProductoHasta"], 0, parameters["idRubro"], parameters["idSubRubro"], parameters["idDeposito"],
            parameters["tipoEstado"]))
            for result in cursor.stored_results():
                for row in result.fetchall():
                    page_number +=1
                    codProducto = row[0]
                    descripcionProducto = row[2]
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
                                           domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number)
                    self.encabezadoReporteInventario(c, height, parameters)
                    y = height - 180  # Reset y-coordinate after drawing the header



                total_fisico += Decimal(item["fisico"])
                total_val_dol += Decimal(item["precioCompra"]) * Decimal(item["stock"]) if item[
                                                                                               "moneda"] == "u$s" else 0
                total_val_pes += Decimal(item["precioCompra"]) * Decimal(item["stock"]) if item[
                                                                                               "moneda"] == "$AR" else 0
                c.drawRightString(55, y, item["codProducto"])
                c.drawString(60, y, item["descripcion"])
                c.drawString(220, y, item["rubro"])
                c.drawRightString(320, y, str(item["fisico"]))
                c.drawRightString(350, y, item["moneda"])
                c.drawRightString(400, y,
                                  f"{Decimal(item['precioCompra']):,.2f}" if item["moneda"] == "u$s" else "0.00")
                c.drawRightString(450, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[
                                                                                                                  "moneda"] == "u$s" else "0.00")
                c.drawRightString(500, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[
                                                                                                                  "moneda"] == "$AR" else "0.00")
                c.drawRightString(570, y, f"{Decimal(item['precioCompra']) * Decimal(item['stock']):,.2f}" if item[
                                                                                                                  "moneda"] == "$AR" else "0.00")
                y -= row_height

            y -= 20
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(320, y, f"Total Fisico: {total_fisico}")
            c.drawRightString(450, y, f"Total Val Dol: {total_val_dol:,.2f}")
            c.drawRightString(570, y, f"Total Val Pes: {total_val_pes:,.2f}")



        c.save()
        #cursor.close()
    # Example usage
    def encabezadoReporte(self, c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa,
                          cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number):
        # Title Right
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(width - 50, height - 50, parameters['titulo'])
        c.setFont("Helvetica", 8)
        c.drawRightString(width - 50, height - 65, "Emitido el: " + str(hoy))
        c.drawRightString(width - 50, height - 80, f"Página: {page_number}")

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
        c.drawImage(logo_path, 15, height - 95, width=70, height=70)

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 103, 580, height - 103)

        # Reset font to regular after header
        c.setFont("Helvetica", 8)

    def encabezadoReporteStockGeneral(self, c,  height, parameters):

        cursor = self.conn.cursor()
        cursor.execute("Select COALESCE(Productos.codProducto, 0) as codigoProductoDesde,COALESCE(Prod.codProducto, 0) as codigoProductoHasta,COALESCE(Productos.descripcion, 0) "
                       "as descripcionProductoDesde,COALESCE(Prod.descripcion, 0) as descripcionProductoHasta,COALESCE(Rubros.descripcion, 0) as descripcionRubro,COALESCE(Depositos.descripcion, 0) "
                       "as descripcionDepositos,SubRubros.descripcion as descripcionSubRubro from Productos left join Productos Prod on Prod.idProductos = 9 "
                       "left join Depositos on Depositos.idDepositos = 6 left join Rubros on Rubros.idRubros = 1 left join SubRubros on SubRubros.idSubRubros =0 where Productos.idProductos =  1")
        datos = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawRightString(580, height - 115, f"Prod Desde: {datos[0]}")
        c.drawRightString(580, height - 125, f"Prod Hasta: {datos[1]}")
        c.drawRightString(580, height - 135, f"Deposito: {datos[5]}")
        '''
        c.drawString(500, height - 115, f"Rubro: {datos[4]}")
        if datos[6] is None:
            c.drawString(500, height - 125, f": ")
        else:
            c.drawString(500, height - 125, f"Sub Rubro: {datos[6]}")
        '''
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
    def encabezadoReporteStockGeneral_2(self, c,  height, parameters):

        cursor = self.conn.cursor()
        cursor.execute("Select COALESCE(Productos.codProducto, 0) as codigoProductoDesde,COALESCE(Prod.codProducto, 0) as codigoProductoHasta,COALESCE(Productos.descripcion, 0) "
                       "as descripcionProductoDesde,COALESCE(Prod.descripcion, 0) as descripcionProductoHasta,COALESCE(Rubros.descripcion, 0) as descripcionRubro,COALESCE(Depositos.descripcion, 0) "
                       "as descripcionDepositos,SubRubros.descripcion as descripcionSubRubro from Productos left join Productos Prod on Prod.idProductos = 9 "
                       "left join Depositos on Depositos.idDepositos = 6 left join Rubros on Rubros.idRubros = 1 left join SubRubros on SubRubros.idSubRubros =0 where Productos.idProductos =  1")
        datos = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawRightString(580, height - 115, f"Prod Desde: {datos[0]}")
        c.drawRightString(580, height - 125, f"Prod Hasta: {datos[1]}")
        c.drawRightString(580, height - 135, f"Deposito: {datos[5]}")
        '''c.drawString(500, height - 115, f"Rubro: {datos[4]}")
        if datos[6] is None:
            c.drawString(500, height - 125, f": ")
        else:
            c.drawString(500, height - 125, f"Sub Rubro: {datos[6]}")
            '''

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
    def encabezadoReporteStockProducto(self, c,  height, parameters, producto):


        descripcionProducto = producto[0]
        codigoProducto = producto[1]
        rubro = producto[2]
        subRubro = producto[3]
        # Encabezado 2
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20, height - 120, f""+str(descripcionProducto))
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
    def encabezadoReporteInventario(self, c,  height, parameters):

        cursor = self.conn.cursor()
        cursor.execute("Select COALESCE(Productos.codProducto, 0) as codigoProductoDesde,COALESCE(Prod.codProducto, 0) as codigoProductoHasta,COALESCE(Productos.descripcion, 0) "
                       "as descripcionProductoDesde,COALESCE(Prod.descripcion, 0) as descripcionProductoHasta,COALESCE(Rubros.descripcion, 0) as descripcionRubro,COALESCE(Depositos.descripcion, 0) "
                       "as descripcionDepositos,SubRubros.descripcion as descripcionSubRubro from Productos left join Productos Prod on Prod.idProductos = 9 "
                       "left join Depositos on Depositos.idDepositos = 6 left join Rubros on Rubros.idRubros = 1 left join SubRubros on SubRubros.idSubRubros =0 where Productos.idProductos =  1")
        datos = cursor.fetchone()

        # Encabezado 2
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, f"Fecha Desde: {parameters.get('fechaDesde', '')}")
        c.drawString(20, height - 125, f"Fecha Hasta: {parameters.get('fechaHasta', '')}")
        c.drawString(20, height - 135, f"Deposito: {datos[5]}")
        c.drawString(300, height - 115, f"Prod Desde: {datos[0]}")
        c.drawString(300, height - 125, f"Prod Hasta: {datos[1]}")
        c.drawString(500, height - 115, f"Rubro: {datos[4]}")
        c.drawString(500, height - 125, f"Sub Rubro: {datos[6]}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 140, 580, height - 140)

        # Table Header
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(50, height - 155, "Codigo")
        c.drawString(60, height - 155, "Descripcion")
        c.drawString(220, height - 155, "Rubro")
        c.drawRightString(320, height - 155, "Fisico")
        c.drawRightString(350, height - 155, "Mon")
        c.drawRightString(400, height - 155, "PC Dol")
        c.drawRightString(450, height - 155, "Val Dol")
        c.drawRightString(500, height - 155, "PC Pes")
        c.drawRightString(570, height - 155, "Val Pes")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 165, 580, height - 165)
        c.setFont("Helvetica", 8)

    def main(self, parameters, reporteCodigo):
        self.generarReportes("reporte_"+str(reporteCodigo)+".pdf", parameters, reporteCodigo)





    #reporte 10 = Stock Inventario
@app.route('/dummy', methods=['GET'])
def dummy():
    import json
    data = {
        "code": "1",
        "status": 200,
        "description": "Generación de reportes en formato PDF.",
        "message": "Reportes PDF, esta activo y funciona correctamente.",
        "reports": ["Reporte General de stock 1", "Reporte de Producto puntual", "Reporte General de stock 2", "Reporte de Inventario"]
    }
    json_output = json.dumps(data, indent=4)
    print(json_output)
    return json_output




@app.route('/generarReporte', methods=['POST'])
def generar_reporte():
    paramsJson = request.get_json()
    parametros=[]
    temp=[]
    parametros = {}
    for key, value in paramsJson.items():
        temp.append({key: value})
    for d in temp:
        parametros.update(d)
    if  request.args.get('tipo') == "inventario":
        reporte_codigo = 10
    elif request.args.get('tipo') == "general-1":
        reporte_codigo = 1
    elif request.args.get('tipo') == "general-2":
        reporte_codigo = 2
    elif request.args.get('tipo') == "producto":
        reporte_codigo = 3

    file_path = f"reporte_{reporte_codigo}_{request.args.get('tipo')}.pdf"
    generador = GeneradorReportes()


    generador.generarReportes(file_path, parametros, reporte_codigo)
    return send_file(file_path)


if __name__ == "__main__":

    #ID REPORTE 2
    parametros={"empresa": "2" ,
                "titulo": "Stock Por Producto",
                "fechaDesde": "2022-01-01",
                "fechaHasta": "2024-10-31",
                "idCteTipo": "0",
                "idDeposito": "6",
                "idProducto": "22",
                "idProductoDesde": "0",
                "idProductoHasta": "0",
                "idRubro": "0",
                "idRubrosGrupos": "3",
                "idSubRubro": "0",
                "orden": "0",
                "tipoEstado": "0"}
    #generador = GeneradorReportes()
    #generador.main(parametros, 3)
    app.run(debug=True, port=6001)