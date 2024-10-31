import csv
'''
# equipara codigo viejo con codigo nuevo
#UPDATE stock_arma_temp, Productos SET stock_arma_temp.codigo_nuevo = Productos.codProducto WHERE ABS(Productos.codProductoOriginal) = stock_arma_temp.codigo_viejo
#SELECT * FROM stock_arma_temp, Productos WHERE ABS(Productos.codProductoOriginal) = stock_arma_temp.codigo_viejo
'''
# Path to the CSV file
csv_file_path = r'E:\Dario\Proyectos\General\Margarita\stock-31-07-2024 agroinsumos\margarita\faltantes.csv'

# Open the CSV file
with open(csv_file_path, mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file, delimiter=';')

    # Skip the header row if it exists
    next(csv_reader, None)

    # Generate INSERT statements
    insert_statements = []
    for row in csv_reader:
        rubro, codigo_nuevo, codigo_viejo, descripcion, cantidad = row
        # Replace comma with dot in the cantidad field
        cantidad = cantidad.replace(',', '.')
        insert_statement = f"INSERT INTO stock_arma_temp (rubro, codigo_nuevo, codigo_viejo, descripcion, cantidad, importado) VALUES ('{rubro}', '{codigo_nuevo}','{codigo_viejo}', '{descripcion}', {cantidad}, 'N');"
        insert_statements.append(insert_statement)

# Print the generated INSERT statements
for statement in insert_statements:
    print(statement)