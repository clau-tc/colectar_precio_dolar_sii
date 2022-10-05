from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep



class ColectDolarSII:

    def __init__(self, name, metadata):
        self.metadata = metadata
        self.name = name
        print('Hola {}, te iré contando el proceso'.format(name))


    def crear_sesion(self, seg):
        print('se crea sesión por cada año consultado, porque Selenium trabaja con elementos web actualizados.')
        driver = webdriver.Chrome(executable_path=self.metadata['path'])
        wait = WebDriverWait(driver, seg)
        return driver, wait

    def construir_pag_web(self, str_year):
        print('Según el número de objetos ingresados en tu lista de años, se creará una url para consultar información sobre precio del dolar')
        """
        :param:
        str_year:list
        años en formato 'YYYY' y más de uno en lista

        :return:
        website: list
        lista de páginas web construidas según años requeridos
        """

        website: List[str] = []
        if len(str_year) <= 1:
            website = [''.join([self.metadata['web'], str_year[0], self.metadata['web_ext']])]
            return website
        else:
            for a in str_year:
                web = ''.join([self.metadata['web'], a, self.metadata['web_ext']])
                website.append(web)
            return website

    def remodelar_tabla(self, tabla, driver):
        print('la tabla recopilada en SII es dinámica, contiene en la última fila el total o prom de los datos.\n'
              'Por esta razón, se remodelan los datos con el propósito de obtener columnas: month, day, year, dolar, prom. \n'
              'Todas estas columnas están al nivel de día, con excepción de prom que señala el prom mensual')

        """
        :param tabla: columnas: días, ene, feb, mar, abr, may... etc. index: 1:31 (días del mes) más 'prom
        |día |ene  |feb  |mar  |abr  |may  |jun  |n    |dic  |
        |----|-----|-----|-----|-----|-----|-----|-----|-----|
        |1   |789.0|789.0|789.0|789.0|789.0|789.0|789.0|789.0|
        |2   |789.0|789.0|789.0|789.0|789.0|789.0|789.0|789.0|
        |n   |789.0|789.0|789.0|789.0|789.0|789.0|789.0|789.0|
        |prom|789.0|789.0|789.0|789.0|789.0|789.0|789.0|789.0|

        :return: df: DataFrame

        |dia|month|year|dolar|prom|
        |---|-----|----|-----|--------|
        |1  | ene |2022|789.0|789.9   |

        """

        year = driver.find_element(By.XPATH, self.metadata['year']).text
        df_reshape = tabla.unstack().reset_index().melt(id_vars=['level_0', 'level_1'])
        df_reshape.columns = ['month', 'day', 'var', 'dolar']
        # se elimina la unidad de medida 'día'
        df_reshape = df_reshape.loc[32:, ['month', 'day', 'dolar']]
        df_reshape.day = df_reshape.day + 1
        df_reshape = df_reshape.reset_index(drop=True)
        # la última fila de cada mes es el prom
        df_prom = df_reshape.copy()
        mask = df_prom[df_prom.day == 32]
        df_prom = mask
        df_prom.reset_index(drop=True, inplace=True)
        df_prom = df_prom.rename(columns={'dolar': 'prom'})
        df_prom = df_prom.loc[:, ['month', 'prom']]

        # se unen
        df = df_reshape.merge(df_prom, how='outer')
        df['year'] = year
        return df

    def colectar_remodelar_dolar(self, website):
        print('En esta etapa se colecta información de página web y se remodelan las tablas obtenidas')
        """
        :param website: lista de sitios webs a scrapear
        :return: tabla
        """
        enc = []
        val = []
        val_filas = []

        if len(website) > 1:

            dfs = pd.DataFrame()

            for w in website:
                driver, wait = self.crear_sesion(15)
                driver.get(w)
                selec_mes = Select(driver.find_element(By.ID, self.metadata['id_sel_mes']))
                selec_mes.select_by_value(self.metadata['valor_mes'])
                encabezados = driver.find_elements(By.XPATH, self.metadata['encabezados'])

                for e in encabezados:
                    enc.append(e.text)
                print(enc)
                valores = driver.find_elements(By.XPATH, self.metadata['valores'])

                for v in valores:
                    val.append(v.text)
                print(val)

                for vf in val:
                    val_filas.append(vf.replace('  ', ' ').split(' '))
                print(val_filas)

                filas = pd.DataFrame(val_filas)
                filas.columns = enc
                df = self.remodelar_tabla(filas, driver)
                driver.close()
                dfs = pd.concat([dfs, df], join='outer', ignore_index=True)
                return dfs

        else:
            driver, wait = self.crear_sesion(15)
            driver.get(website[0])
            selec_mes = Select(driver.find_element(By.ID, self.metadata['id_sel_mes']))
            selec_mes.select_by_value(self.metadata['valor_mes'])
            encabezados = driver.find_elements(By.XPATH, self.metadata['encabezados'])

            for e in encabezados:
                enc.append(e.text)
            print(enc)
            valores = driver.find_elements(By.XPATH, self.metadata['valores'])

            for v in valores:
                val.append(v.text)
            print(val)

            for vf in val:
                val_filas.append(vf.replace('  ', ' ').split(' '))
            print(val_filas)

            filas = pd.DataFrame(val_filas)
            filas.columns = enc

            df = self.remodelar_tabla(filas, driver)

            driver.close()
            return df

#%%
