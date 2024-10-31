from flask import Flask, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from decimal import Decimal
from conn.FacturacionConnection import FacturacionConnection as FacturacionConnnection
from datetime import datetime, timedelta
from reportlab.lib.units import inch
from reportlab.lib.colors import grey, lightgrey
#import logging
#logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
class GeneradorComprobantes(FacturacionConnnection ):
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

    def generarComprobante(self, file_path,  parameters, comprobante,  nombrePdf,  modulo):

        print("::: Iniciando generacion de comprobante ("+str(comprobante)+")...")
        hoy = datetime.today().date()
        cursor = self.conn.cursor()
        neto = Decimal(0)
        #traigo datos de la empresa

        cursor.execute("SELECT prefijoEmpresa, nombre, descripcion, domicilio, cuit, telefono, situacionIva FROM Empresas WHERE idEmpresa = 2")
        empresa = cursor.fetchone()
        prefijoEmpresa = empresa[0]
        nombreEmpresa = empresa[1]
        descripcionEmpresa = empresa[2]
        domicilioEmpresa = empresa[3]
        cuitEmpresa = empresa[4]
        empresaSituacionIva = empresa[6]
        idFactCab = comprobante
        algoritmoImagenQr = ""
        codigoVerificador = "0"
        tipoComprobanteAfip = "0"
        copia = "1"
        imagenQr = ""
        data = []
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        page_number = 1
        sql = (
            "SELECT "
            "LPAD(SUBSTRING(FactCab.numero, 1, LENGTH(FactCab.numero) - 8), 4, '0') AS prefijoComprobante, "
            "SUBSTRING(FactCab.numero, -8) AS numeroComprobante, "
            "FactCab.cuit AS cuitCliente, "
            "FactCab.fechaEmision AS fechaEmisionComprobante, "
            "FactCab.nombre AS nombreCilente, "
            "FactCab.cai AS caiComprobante, "
            "FactCab.fechaVto AS fechaVencimientoComprobante, "
            "FactCab.sitIVA AS situacionIvaCliente, "
            "FactCab.idListaPrecios AS listaPrecios, "
            "FactCab.letra AS letra, "
            "FactCab.cai AS cae, "
            "FactCab.caiVto AS caeVto, "
            "FactCab.codigoAfip AS codigoAfip, "
            "FactCab.cotDolar AS cotDolar, "
            "FactCab.idPadron AS ctaCtePadron, "
            "FactCab.Observaciones AS observaciones, "
            "FactCab.domicilio AS domicilioPadron, "
            "FactCab.codigoPostal AS codigoPostal, "
            "FactCab.pesificado AS pesificado, "
            "FactCab.dolarizadoAlVto AS dolarizadoAlVto, "
            "FactCab.interesMensualCompra AS interesMensualCompra, "
            "FactCab.canjeInsumos AS canjeInsumos, "
            "FactCab.tipoCambio AS tipoCambio, "
            "FactCab.idCteTipo AS idCteTipo, "
            "LPAD(SUBSTRING(FactCab.numeroAfip, 1, LENGTH(FactCab.numeroAfip) - 8), 4, '0') AS prefijoComprobanteAfip, "
            "SUBSTRING(FactCab.numeroAfip, -8) AS numeroComprobanteAfip, "
            "FactDetalle.detalle AS detalleProducto, "
            "FactDetalle.cantidad AS cantidad, "
            "FactDetalle.precio AS precio, "
            "FactDetalle.codProducto AS codigoProducto, "
            "FactDetalle.importe AS importe, "
            "FactDetalle.descuento AS descuento, "
            "FactDetalle.precioDesc AS precioDesc, "
            "FactDetalle.unidadDescuento AS unidadDescuento, "
            "CteTipo.descCorta AS descripcionCortaCteTipo, "
            "CteTipo.descripcion AS descripcionCteTipo, "
            "CteTipo.detalleReporte AS detalleReporte, "
            "Empresas.nombre AS nombreEmpresa, "
            "Empresas.descripcion AS descripcionEmpresa, "
            "Empresas.domicilio AS domicilioEmpresa, "
            "Empresas.cuit AS cuitEmpresa, "
            "Empresas.iibb AS ingBrutosEmpresa, "
            "Empresas.telefono AS telefono, "
            "Empresas.codigoPostal AS codigoPostalEmpresa, "
            "Empresas.situacionIva AS situacionIvaEmpresa, "
            "SisOperacionComprobantes.leyenda1 AS leyenda1, "
            "SisOperacionComprobantes.leyenda2 AS leyenda2, "
            "SisOperacionComprobantes.leyenda3 AS leyenda3, "
            "SisOperacionComprobantes.leyenda4 AS leyenda4, "
            "SisMonedas.descripcion AS moneda, "
            "SisMonedas.idMonedaAfip AS monedaAfip, "
            "IF(SisMonedas.descripcion = '$AR', 1, FactCab.cotDolar) AS cotizacionMoneda, "
            "SisTipoOperacion.descripcion AS tipoOperacion, "
            "SisComprobantes.idSisComprobantes AS idSisComprobante, "
            "PadronGral.nombre AS apellido, "
            "IFNULL(FactFormaPago.detalle, NULL) AS detalleFormaPago, "
            "LPAD(SUBSTRING(comprobanteImputado.numero, 1, LENGTH(comprobanteImputado.numero) - 8), 4, '0') AS prefijoComprobanteImputado, "
            "SUBSTRING(comprobanteImputado.numero, -8) AS numeroComprobanteImputado, "
            "SisComprobantes.idSisModulos AS modulo "
            "FROM FactCab "
            "INNER JOIN CteTipo ON FactCab.idCteTipo = CteTipo.idCteTipo "
            "INNER JOIN Empresas ON CteTipo.idEmpresa = Empresas.idEmpresa "
            "INNER JOIN FactDetalle ON FactCab.idFactCab = FactDetalle.idFactCab "
            "INNER JOIN SisMonedas ON SisMonedas.idMoneda = FactCab.idmoneda "
            "INNER JOIN SisTipoOperacion ON FactCab.idSisTipoOperacion = SisTipoOperacion.idSisTipoOperacion "
            "INNER JOIN SisOperacionComprobantes ON FactCab.idSisOperacionComprobantes = SisOperacionComprobantes.idSisOperacionComprobantes "
            "LEFT JOIN FactImputa ON FactDetalle.idFactDetalle = FactImputa.idFactDetalleImputa "
            "LEFT JOIN SisComprobantes ON SisOperacionComprobantes.idSisComprobantes = SisComprobantes.idSisComprobantes "
            "LEFT JOIN PadronGral ON FactCab.idPadron = PadronGral.idPadronGral "
            "LEFT JOIN FactDetalle AS detalleImputado ON detalleImputado.idFactDetalle = FactImputa.idFactDetalle "
            "LEFT JOIN FactCab AS comprobanteImputado ON comprobanteImputado.idFactCab = detalleImputado.idFactCab "
            "LEFT JOIN FactFormaPago ON FactCab.idFactCab = FactFormaPago.idFactCab "
            "WHERE FactCab.idFactCab = %s"
        )






        if comprobante is not None and comprobante > 0:
            cursor.execute(sql, (idFactCab,))
            data = list(cursor.fetchall())
            importeFormaPago = 0
            for row in data:

                fechaEmision = row[3]
                nroComprobante = row[0] + "-" + row[1]
                descripcionCteTipo = row[35]
                listaPrecios = row[8]
                moneda = row[49]
                tipoOperacion = row[52]
                ctactePadron = row[14]
                empresaCodigoPostal = row[43]
                empresaTelefonos = row[42]
                letraComprobante= row[9]
                codigoAfip = row[12]
                detalleReporte = row[36]
                ingBrutosEmpresa = row[41]
                clienteNombre = row[4]
                clienteCuit = row[2]
                clienteDomicilio = row[16]
                clienteCodigoPostal = row[17]
                clienteSituacionIva = row[7]
                modulo =row[58]

            if modulo == 1:
                # compra
                self.encabezadoComprobantesCompra(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                        domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                        page_number, nroComprobante, fechaEmision, descripcionCteTipo, detalleReporte, moneda, tipoOperacion, ctactePadron, listaPrecios,
                                        empresaCodigoPostal, empresaTelefonos, letraComprobante, codigoAfip, ingBrutosEmpresa, clienteNombre, clienteCuit, clienteDomicilio, clienteCodigoPostal, clienteSituacionIva)
            elif modulo == 2:
                # venta
                self.encabezadoComprobantesVenta(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                                  domicilioEmpresa, cuitEmpresa, empresaSituacionIva, hoy, parameters,
                                                  page_number, nroComprobante, fechaEmision, descripcionCteTipo,
                                                  detalleReporte, moneda, tipoOperacion, ctactePadron, listaPrecios,
                                                  empresaCodigoPostal, empresaTelefonos, letraComprobante, codigoAfip,
                                                  ingBrutosEmpresa, clienteNombre, clienteCuit, clienteDomicilio,
                                                  clienteCodigoPostal, clienteSituacionIva)

            # Draw header with grey background
            c.setFillColor(lightgrey)
            c.rect(20, height - 182, width - 40, 20, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(25, height - 173, "CODIGO")
            c.drawString(70, height - 173, "DESCRIPCION")
            c.drawRightString(305, height - 173, "NRO COMP")
            c.drawRightString(370, height - 173, "CANT")
            c.drawRightString(420, height - 173, "BON")
            c.drawRightString(500, height - 173, "PRECIO")
            c.drawRightString(580, height - 173, "IMPORTE")
            c.setFont("Helvetica", 8)
            y = height - 200
            row_height = 15

            for item in data:

                page_number += 1
                codProducto = item[25]
                detalleProducto = item[26]
                cantidad = item[27]
                prefijoComprobanteImputado = item[56]
                numeroComprobanteImputado = item[57]
                if prefijoComprobanteImputado is None:
                    prefijo = 0
                else:
                    prefijo = prefijoComprobanteImputado[:4]

                if numeroComprobanteImputado is None:
                    nro = 0
                else:
                    nro = numeroComprobanteImputado[:8]

                numeroComprobanteMuestra= str(prefijo) + "-" + str(nro)
                descuento = row[31]
                unidadDescuento = row[33]
                if descuento == None:
                    descuento = 0
                if unidadDescuento == None or unidadDescuento == "":
                    unidadDescuento = 0
                bonificacion = descuento+unidadDescuento

                precio = item[28]
                importe = item[30]
                neto += Decimal(importe)
                c.drawString(25, y, str(codProducto))
                c.drawString(70, y, str(detalleProducto))
                c.drawString(250, y, str(numeroComprobanteMuestra))
                c.drawString(350, y, str(f"{Decimal(cantidad) :,.0f}"))
                c.drawRightString(420, y, str(f"{Decimal(bonificacion) :,.2f}"))
                c.drawRightString(500, y, str(f"{Decimal(precio) :,.2f}"))
                c.drawRightString(580, y, str(f"{Decimal(importe) :,.2f}"))
                y -= row_height



            # Table Data
            page_number = 1
            y = height - 180
            c.setFont("Helvetica", 8)
            y = height - 180  # Starting y-coordinate
            row_height = 15  # Height of each row
            available_height = height - 200



        # Forma Pago
        sql = ("select FactFormaPago.fechaPago as fechaPago, FactFormaPago.diasPago as diasPago,"
               "FactFormaPago.importe as importeFormaPago, FactFormaPago.porcentaje as porcentajeFormaPago, "
               "FactFormaPago.detalle as detalleFormaPago,FormaPago.tipo as tipoFormaPago, FormaPago.descripcion as descripcionFormaPago "
               "from FactFormaPago left join FormaPago on FormaPago.idFormaPago = FactFormaPago.idFormaPago "
               "where FactFormaPago.idFactCab = %s")
        cursor = self.conn.cursor()
        cursor.execute(sql, (idFactCab,))
        dataFp = list(cursor.fetchall())
        y = height - 200
        c.setFillColor(lightgrey)
        c.rect(15, height - 600, width - 30, 15, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(25, height - 595, "FORMA DE PAGO")
        c.drawString(305, height - 595, "FECHA DE PAGO")
        c.drawRightString(450, height - 595, "IMPORTE")
        c.drawRightString(580, height - 595, "INTERES")
        c.setFont("Helvetica", 7)
        y = height - 600
        row_height = 10

        for row in dataFp:
            fechaPago = row[0]
            diasPago = row[1]
            importeFormaPago += Decimal(row[2])
            porcentajeFormaPago = row[3]
            detalleFormaPago = row[4]
            tipoFormaPago = row[5]
            descripcionFormaPago = row[6]

            c.drawString(25, y-row_height, str(descripcionFormaPago)+" "+str(detalleFormaPago))
            c.drawString(305, y-row_height, str(fechaPago))
            c.drawRightString(450, y-row_height, str(f"{Decimal(importeFormaPago) :,.2f}"))
            c.drawRightString(580, y-row_height, str(f"{Decimal(porcentajeFormaPago) :,.2f}"))
            y -= row_height

        self.agregarPieySubTotales(c, idFactCab, neto, width, height)

        c.save()

    def agregarPieySubTotales(self, c, idFactCab, neto, width, height):

        cursor = self.conn.cursor()
        sql=("select FactPie.detalle as detallePie, FactPie.importe as importePie, FactPie.porcentaje as porcentajePie, "
             "FactPie.baseImponible as baseImponible, FactPie.operador as operador from FactPie where FactPie.idFactCab = %s")
        cursor.execute(sql, (idFactCab,))
        footer_y = 40  # y-coordinate for the footer
        c.setFont("Helvetica", 8)
        y = height - 650
        row_height = 10
        c.setFillColor(lightgrey)
        c.rect(15, y - row_height, width - 30, 15, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(25, (y - row_height)+5, "SUB TOTALES")
        c.setFont("Helvetica", 8)
        y -= row_height+5
        c.drawString(25, y - row_height, "NETO")
        c.drawRightString(width - 25, y - row_height, f"{Decimal(neto):,.2f}")
        y -= row_height
        total = 0
        for row in cursor.fetchall():
            concepto = row[0]
            importePie = row[1]
            total +=  Decimal(importePie)
            porcentajePie = row[2]
            baseImponible = row[3]
            c.setFont("Helvetica", 8)

            c.drawString(25, y-row_height, concepto)
            c.drawRightString(width - 25,y-row_height, f"{Decimal(importePie):,.2f}")
            y -= row_height
            #c.drawString(25, footer_y - 15, "Total:")
            #c.drawRightString(width - 25, footer_y - 15, f"{Decimal(total):,.2f}")

            # Optionally, add a line above the footer
            c.setLineWidth(1)
            c.setStrokeColor(colors.grey)
            c.line(20, footer_y + 10, width - 20, footer_y + 10)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(25, y - row_height, "TOTAL")
        c.drawRightString(width - 25, y - row_height, f"{Decimal(total+neto):,.2f}")


    def encabezadoComprobantesCompra(self, c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa,   cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number, nroComprobante, fechaEmision, descripcionCteTipo, detalleReporte, moneda, tipoOperacion, ctactePadron, listaPrecios, empresaCodigoPostal, empresaTelefonos, letraComprobante, codigoAfip, ingBrutosEmpresa, clienteNombre, clienteCuit, clienteDomicilio, clienteCodigoPostal, clienteSituacionIva):

         # Title Right
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(width - 20, height - 30, descripcionCteTipo)
        c.setFont("Helvetica", 8)
        c.drawRightString(width - 80, height - 45, "Nro:")
        c.drawRightString(width - 20, height - 45,  str(nroComprobante))
        c.drawRightString(width - 80 , height - 55, "Fecha emisión:")
        c.drawRightString(width - 20, height - 55,  str(fechaEmision))


        # Letra
        square_size = 40
        square_x = square_x = (width - square_size) / 2
        square_y = height - 60
        c.rect(square_x, square_y, square_size, square_size, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(square_x + square_size / 2, (square_y + square_size / 2)-5, str(letraComprobante))


        c.setFont("Helvetica", 6)
        c.drawRightString((square_x + square_size / 2)+10, square_y-10, "COD: " + str(codigoAfip))





        # Title Left
        c.setFont("Helvetica-Bold", 11)
        c.drawString(90, height - 30, str(nombreEmpresa))
        c.setFont("Helvetica", 8)
        c.drawString(90, height - 40, str(descripcionEmpresa))


        c.setFont("Helvetica", 7)
        c.drawString(90, height - 60, str("Dirección: "+domicilioEmpresa))
        c.drawString(90, height - 70, str("Tel: " + str(empresaTelefonos)))
        c.drawString(90, height - 80, str("CP: " + str(empresaCodigoPostal)))

    # Logo
        logo_path = "img/" + str(prefijoEmpresa) + ".png"
        c.drawImage(logo_path, 15, height - 90, width=70, height=70)

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 103, width-20, height - 103)

        # Reset font to regular after header

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 120, "NOMBRE:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 120, str(clienteNombre))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 130, "CUIT:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 130, str(clienteCuit))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 140, "DOMICILIO:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 140, str(clienteDomicilio)+" CP: "+str(clienteCodigoPostal))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 150, "IVA:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 150, str(clienteSituacionIva))

        c.drawRightString(width - 80, height - 120, "Lista de precios:")
        if listaPrecios == None:
            listaPrecios = "Sin Lista"
        else:
            listaPrecios = str(listaPrecios)
        c.drawRightString(width - 20, height - 120, str(listaPrecios))
        c.drawRightString(width - 80, height - 130, "Moneda:")
        c.drawRightString(width - 20, height - 130, str(moneda))
        c.drawRightString(width - 80, height - 140, "Operacion:")
        c.drawRightString(width - 20, height - 140, str(tipoOperacion))
        c.drawRightString(width - 80, height - 150, "Cuenta:")
        c.drawRightString(width - 20, height - 150, str(ctactePadron))

        #c.setLineWidth(1)
        #c.setStrokeColor(colors.grey)
        #c.line(20, height - 160, width-20, height - 160)



    def encabezadoComprobantesVenta(self, c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, domicilioEmpresa,   cuitEmpresa, empresaSituacionIva, hoy, parameters, page_number, nroComprobante, fechaEmision, descripcionCteTipo, detalleReporte, moneda, tipoOperacion, ctactePadron, listaPrecios, empresaCodigoPostal, empresaTelefonos, letraComprobante, codigoAfip, ingBrutosEmpresa, clienteNombre, clienteCuit, clienteDomicilio, clienteCodigoPostal, clienteSituacionIva):

         # Title Right
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(width - 50, height - 30, descripcionCteTipo)
        c.setFont("Helvetica", 8)
        c.drawRightString(width - 110, height - 45, "Nro:")
        c.drawRightString(width - 50, height - 45,  str(nroComprobante))
        c.drawRightString(width - 110 , height - 55, "Fecha emisión:")
        c.drawRightString(width - 50, height - 55,  str(fechaEmision))


        c.drawRightString(width - 100, height - 75, "Cuit:")
        c.drawRightString(width - 50, height - 75, str(cuitEmpresa) )
        c.drawRightString(width - 100, height - 85, "IVA:")
        c.drawRightString(width - 50, height - 85, str(empresaSituacionIva))
        c.drawRightString(width - 100, height - 95, "IIBB:")
        c.drawRightString(width - 50, height - 95,  str(ingBrutosEmpresa))

        # Letra
        square_size = 40
        square_x = square_x = (width - square_size) / 2
        square_y = height - 60
        c.rect(square_x, square_y, square_size, square_size, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(square_x + square_size / 2, (square_y + square_size / 2)-5, str(letraComprobante))


        c.setFont("Helvetica", 6)
        c.drawRightString((square_x + square_size / 2)+10, square_y-10, "COD: " + str(codigoAfip))





        # Title Left
        c.setFont("Helvetica-Bold", 11)
        c.drawString(90, height - 30, str(nombreEmpresa))
        c.setFont("Helvetica", 8)
        c.drawString(90, height - 40, str(descripcionEmpresa))


        c.setFont("Helvetica", 7)
        c.drawString(90, height - 60, str("Dirección: "+domicilioEmpresa))
        c.drawString(90, height - 70, str("Tel: " + str(empresaTelefonos)))
        c.drawString(90, height - 80, str("CP: " + str(empresaCodigoPostal)))

    # Logo
        logo_path = "img/" + str(prefijoEmpresa) + ".png"
        c.drawImage(logo_path, 15, height - 90, width=70, height=70)

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 103, 580, height - 103)

        # Reset font to regular after header

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 120, "NOMBRE:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 120, str(clienteNombre))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 130, "CUIT:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 130, str(clienteCuit))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 140, "DOMICILIO:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 140, str(clienteDomicilio)+" CP: "+str(clienteCodigoPostal))

        c.setFont("Helvetica-Bold", 8)
        c.drawString(20, height - 150, "IVA:")
        c.setFont("Helvetica", 8)
        c.drawString(70, height - 150, str(clienteSituacionIva))

        c.drawRightString(width - 110, height - 120, "Lista de precios:")
        if listaPrecios == None:
            listaPrecios = "Sin Lista"
        else:
            listaPrecios = str(listaPrecios)
        c.drawRightString(width - 50, height - 120, str(listaPrecios))
        c.drawRightString(width - 110, height - 130, "Moneda:")
        c.drawRightString(width - 50, height - 130, str(moneda))
        c.drawRightString(width - 110, height - 140, "Operacion:")
        c.drawRightString(width - 50, height - 140, str(tipoOperacion))
        c.drawRightString(width - 110, height - 150, "Cuenta:")
        c.drawRightString(width - 50, height - 150, str(ctactePadron))

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 160, 580, height - 160)










    def main(self, parameters, comprobante, nombrePdf, modulo):
        self.generarComprobante("comprobante_"+str(comprobante)+".pdf", parameters, comprobante, nombrePdf, modulo)





    #reporte 10 = Stock Inventario
@app.route('/dummy', methods=['GET'])
def dummy():
    import json
    data = {
        "code": "1",
        "status": 200,
        "description": "Generador de Comprobantes en PDF",
        "Metodos expuestos" : "[dummy], [generarComprobante]",
        "message": "Generación de comprobantes en PDF, esta activo y funciona correctamente.",

    }
    json_output = json.dumps(data, indent=4)
    print(json_output)
    return json_output




@app.route('/generarComprobante', methods=['POST'])
def generarComprobante():
    try:
        paramsJson = request.get_json()
        parametros = {}
        for key, value in paramsJson.items():
            parametros[key] = value

        comprobante = paramsJson.get('idFactCab')
        print(":::: idFactCab :: " + str(comprobante))
        nombrePdf = paramsJson.get('nombrePdf')
        modulo = paramsJson.get('modulo')

        file_path = f"comprobante_{comprobante}.pdf"
        generador = GeneradorComprobantes()
        generador.generarComprobante(file_path, parametros, comprobante, nombrePdf, modulo)
        return send_file(file_path)
    except Exception as e:
        return jsonify({"error": "Error Interno: " + str(e)}), 500

if __name__ == "__main__":

    #ID REPORTE 2
    parametros={"empresa": "2" ,
                "titulo": "Stock Por Producto",
                "fechaDesde": "2024-01-01",
                "fechaHasta": "2024-10-21",
                "idCteTipo": "0",
                "idDeposito": "0",
                "idProducto": "9",
                "idProductoDesde": "0",
                "idProductoHasta": "0",
                "idRubro": "0",
                "idRubrosGrupos": "0",
                "idSubRubro": "0",
                "orden": "0",
                "tipoEstado": "0"}
    #generador = GeneradorComprobantes()
    #generador.main(parametros, 2525, "general", 1)
    app.run(debug=True, port=6001)

#if __name__ == "__main__":
    #app.run(debug=True, port=6001)