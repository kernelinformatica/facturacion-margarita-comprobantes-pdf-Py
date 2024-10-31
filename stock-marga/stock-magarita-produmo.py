from conn.FacturacionConnection import FacturacionConnection as FacturacionConnnection
from datetime import datetime, timedelta


# CORS(app)
class StockProdumo(FacturacionConnnection):
    def __init__(self):
        super().__init__()
        self.datos = []
        self.hoy = datetime.now()
        self.connFacturacion = FacturacionConnnection()

    def levantoPreDatosDeOrigen(self):
        print("::: Iniciando ..")
        hoy = datetime.today().date()
        cursor = self.conn.cursor()
        cursor.execute("SELECT rubro, codigo_nuevo AS codProducto, descripcion, cantidad FROM stock_arma_temp where importado = 'N'")
        rows = cursor.fetchall()
        insert_statements = []
        for row in rows:
            self.datos.append(row)

            codigoProducto = row[1]
            if codigoProducto is not None:
                cursor.execute(f'SELECT idProductos FROM Productos WHERE codProducto = {codigoProducto}')
                producto = cursor.fetchall()
                if producto:
                    idProducto = producto[0][0]
                else:
                    idProducto =0

                descripcion = row[2]
                cantidad = row[3]
                fecha =  '2024-07-31'
                #xxx = Produmo , no ejecutar dos veces porque duplica no le puse el control
                insert_statement = f"INSERT INTO xxxx (numero, item, fecha, detalle, cantidad, idCteTipo, idDepositos, idProductos, idFactDetalle, stock)VALUES (20240731, 0,'2024-07-31' ,'Inventario Físico', {cantidad}, 89, 6, {idProducto}, 0, 1);"
                cursor.execute(insert_statement)
                self.conn.commit()
                print("Insertado", row)
            else:
                print("Atención  codigoProducto no es válido:", row)




    def main(self):
            self.levantoPreDatosDeOrigen()









if __name__ == "__main__":
    stock = StockProdumo()
    stock.main()
