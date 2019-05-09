#Nos llega la información de openfda en json y trabajaremos en json.loads
#Vamos a importar socketserver ya que vamos a producir la comunicacion a traves de un socket.
#Importamos http.client para establecer que vamos a ser a la vez servidor y cliente de openfda
import http.server
import http.client
import json
import socketserver

PORT = 8000
INDEX_FILE = "index.html" #Archivo con el formulario a rellenar


class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    # Usamos el servidor que emplea herencia visto en clase.
    OPENFDA_API_URL="api.fda.gov" #Empleamos API que es un conjunto de recursos que podemos emplear para multitud de funciones.
    OPENFDA_API_EVENT="/drug/label.json"
    OPENFDA_API_DRUG='&search=active_ingredient:'
    OPENFDA_API_COMPANY='&search=openfda.manufacturer_name:'

    # Construimos la web del formulario como un string.
    def get_formulario(self):
        with open(INDEX_FILE, "r") as f:
            index_html = f.read() #Leemos y devolvermos el formulario

        return index_html

    def dar_info (self, infor):#Funcion a la que le llega la información y la transforma en html
        mensaje_html = """  <html><head><title>...OpenFDA...</title></head>
        <body><ul>"""

        for i in infor:
            mensaje_html += "<li>" + i + "</li>"

        mensaje_html += """</ul></body></html>"""

        return mensaje_html

    def dar_resultado_general (self, limit=10):
        conn = http.client.HTTPSConnection(self.OPENFDA_API_URL)
        conn.request("GET", self.OPENFDA_API_EVENT + "?limit="+str(limit))
        print (self.OPENFDA_API_EVENT + "?limit="+str(limit))
        r1 = conn.getresponse()
        data_raw = r1.read().decode("utf8")
        data = json.loads(data_raw)
        resultados = data['results']
        return resultados

    #Creamos una función principal que agrupa las funciones anteriores
    def do_GET(self):
        recursos = self.path.split("?") #Dividimos el path para sacar los parámetros
        if len(recursos) > 1: #Buscamos los parametros para ver si hay un límite
            param = recursos[1]
        else:
            param = ""

        limit = 1

        # Si hay parámetros, obtenermos el valor del limit
        if param:
            print('HAY PARAMETROS')
            limite = param.split("=")
            if limite[0] == "limit":
                limit = int(limite[1])
                print("Limit: {}".format(limit))
        else:
            print("SIN PARAMETROS") #Cogerá el limit por defecto


        #En función del path se ejecutará una función u otra

        # Enviamos el formulario
        if self.path=='/':
            print("Enviando formulario...")
            # Mandamos informacion del estado del mensaje
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            formulario = self.get_formulario()
            self.wfile.write(bytes(formulario, "utf8"))

        #Si pedimos la lista de fármacos
        elif 'listDrugs' in self.path:
            print('Buscando la lista de medicamentos...')
            #Todo ha ido muy bien
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            print("El límite de medicamentos es: ", limit)

            #Lista para almacenar los datos de los fármacos
            farmacos = []
            resultados = self.dar_resultado_general(limit)
            for resultado in resultados:
                if ('generic_name' in resultado['openfda']):
                    farmacos.append (resultado['openfda']['generic_name'][0])
                else:
                    farmacos.append('Desconocido')
            info_html = self.dar_info(farmacos)

            self.wfile.write(bytes(info_html, "utf8"))

        #Si pedimos la lista de compañias
        elif 'listCompanies' in self.path:
            print("Buscando lista de compañías...")
            #Todo va muy bien
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            #Creamos una lista vaci para almacenar los datos
            lista_companias = []
            resultados = self.dar_resultado_general (limit)
            #Iteramos sobre cada elemento de la información
            for resultado in resultados:
                if ('manufacturer_name' in resultado['openfda']):
                    lista_companias.append (resultado['openfda']['manufacturer_name'][0])
                else:
                    lista_companias.append('Desconocido')
            #Enviamos información al cliente
            info_html = self.dar_info(lista_companias)
            self.wfile.write(bytes(info_html, "utf8"))

        #Si queremos buscar un farmaco
        elif 'searchDrug' in self.path:
            print("Buscando farmacos con el principio activo introducido...")
            # Todo ha ido muy bien
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            limit = 10

            #Dividimos el path por cada =
            drug = self.path.split('=')[1] #Cogemos el segundo elemento, el principio activo introducido en el formulario
            #Creamos una lista vacia para almacenar los datos
            lista_farmacos = []
            #Establecemos conexión con servidor
            conn = http.client.HTTPSConnection(self.OPENFDA_API_URL)
            #Creamos una URL con la petición indicando el farmaco que deseamos
            conn.request("GET", self.OPENFDA_API_EVENT + "?limit="+str(limit) + self.OPENFDA_API_DRUG + drug)
            r1 = conn.getresponse() #Obtenemos respuesta y sacamos la información
            respuesta = r1.read()
            info = respuesta.decode("utf8")
            biblioteca_datos = json.loads(info)
            drugs = biblioteca_datos['results'] #drugs es un diccionario con la informacion que vamos a obtenerself.
            #Cogemos el nombre del medicamento si está en el diccionario, y sino ponemos "Desconocido"

            for resultado in drugs:
                if ('generic_name' in resultado['openfda']):
                    lista_farmacos.append(resultado['openfda']['generic_name'][0])
                else:
                    lista_farmacos.append('Desconocido')

            #Enviamos información al cliente
            info_html = self.dar_info(lista_farmacos)
            self.wfile.write(bytes(info_html, "utf8"))
            print('Enviando los datos obtenidos...')

        #Si queremos buscar una compañía. Mismo procedimiento que en la búsqueda de fármacos
        elif 'searchCompany' in self.path:
            print("Buscando compañías...")
            # Todo va muy bien
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            limit = 10

            #Dividimos el path y cogemos el segundo elemento, el nombre de la compañía.
            company = self.path.split('=')[1]
            #Creamos una lista vacía para almacenar los datos
            lista_companias = []

            #Establecemos conexión con el servidor
            conn = http.client.HTTPSConnection(self.OPENFDA_API_URL)
            conn.request("GET", self.OPENFDA_API_EVENT + "?limit=" + str(limit) + self.OPENFDA_API_COMPANY + company) #La petición contiene la compañía que queremos
            r1 = conn.getresponse()
            respuesta = r1.read()
            info = respuesta.decode("utf8")
            biblioteca_datos = json.loads(info)
            companies = biblioteca_datos['results']

            for resultado in companies:
                if 'manufacturer_name' in resultado['openfda']:
                    lista_companias.append(resultado['openfda']['manufacturer_name'][0])
                else:
                    lista_companias.append('Desconocido')

            #Enviamos la informacion al cliente
            info_html = self.dar_info(lista_companias)
            self.wfile.write(bytes(info_html, "utf8"))
            print("Enviamos los datos obtenidos...")

        elif 'listWarnings' in self.path:
            print("Buscando listado advertencias...")
            # Todo va muy bien
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            #Creamos una lista vacía para almacenar los datos
            lista_warnings = []
            #Establecemos conexión con el servidor y obtenemos los datos
            resultados = self.dar_resultado_general(limit)
            #Iteramos sobre los datos para obtener las advertencias
            for resultado in resultados:
                if ('warnings' in resultado):
                    lista_warnings.append (resultado['warnings'][0])
                else:
                    lista_warnings.append('Desconocido')
            #Enviamos respuesta
            info_html = self.dar_info(lista_warnings)
            self.wfile.write(bytes(info_html, "utf8"))

        #Extensión IV: Redirect y Authentication
        elif 'redirect' in self.path:
            print('Mandamos la redireccion a la página principal...')
            self.send_response(302)
            self.send_header('Location', 'http://localhost:'+str(PORT))
            self.end_headers()

        elif 'secret' in self.path:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Mi servidor"')
            self.end_headers()

        #Extensión II: Error 404, Not found
        # El recurso solicitado no se encuentra en el servidor
        else:
            self.send_error(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("I don't know '{}'.".format(self.path).encode())
        return


socketserver.TCPServer.allow_reuse_address= True #Reservamos la IP y el puerto donde el servidor va a escuchar. Permite que se renueve el puerto ya usado

# Handler: instancia de la clase que sabe responder a un do get, manejador de http.
# El manejador no está siempre ejecutando, sino que cada vez que llega algo al puerto, este se encarga de gestionar la respuesta
Handler = testHTTPRequestHandler
httpd = socketserver.TCPServer(("", PORT), Handler) # Asocia una IP y un puerto al manejador de peticiones. Cuando llega una petición a la IP y al puerto el programa le dice al manejador que atienda
print("Sirviendo en el puerto...", PORT)

try:
    httpd.serve_forever() #Línea para que empiece a funcionr el programa
except KeyboardInterrupt:
    print("El programa se ha interrumpido")
    httpd.close
