#!/usr/bin/python
# -*- coding: utf8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Yorik van Havre <yorik@uncreated.net>            *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

"""PriceAPI - A python API to retrieve and search prices of construction materials and services."""

__title__  = "Price API"
__author__ = "Yorik van Havre"
__url__    = "http://yorik.uncreated.net"


import sys,os,urllib2,tempfile,csv,zipfile,getopt,unicodedata


class source:

    """Base class for price sources"""

    def __init__(self):
        self.URL = None
        self.Name = None
        self.Description = None
        self.City = None
        self.Country = None
        self.Month = None
        self.Year = None
        self.refURL = None
        self.Currency = None
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []
        self.CUB = None

    def __repr__(self):
        s = "Price source"
        if not self.Name:
            s += " (not set)"
        else:
            s += ": "+str(self.Name)
        if self.City and self.Country:
            s += " - "+str(self.City)+", "+str(self.Country)
        if self.Year and self.Month:
            s += " ("+str(self.Month).zfill(2)+"/"+str(self.Year)+")"
        if self.codes:
            s += " - "+str(len(self.codes))+" lines of data"
        else:
            s += " - empty"
        return s

    def printline(self,ln):
        if ln < len(self.codes):
            print self.codes[ln],"/",self.descriptions[ln],"/",self.values[ln],"/",self.units[ln]

    def save(self,filename=None):
        if not filename:
            filename = os.path.dirname(os.path.abspath(__file__))+os.sep+"data"+os.sep+self.defaultfile
        if self.codes:
            csvfile = open(filename, 'wb')
            csvw = csv.writer(csvfile)
            for i in range(len(self.codes)):
                if isinstance(self.descriptions[i],unicode):
                    d = self.descriptions[i].encode("utf8")
                else:
                    d = self.descriptions[i]
                if isinstance(self.units[i],unicode):
                    u = self.units[i].encode("utf8")
                else:
                    u = self.units[i]
                #print self.codes[i],d,self.values[i],self.units[i]
                csvw.writerow([self.codes[i],d,self.values[i],u])
            csvfile.close()

    def load(self,filename):
        csvfile = open(filename, 'rb')
        csvr = csv.reader(csvfile)
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []
        for row in csvr:
            self.codes.append(row[0])
            self.descriptions.append(row[1])
            self.values.append(row[2])
            self.units.append(row[3])
        csvfile.close()

    def loaddefault(self,filename):
        default = os.path.dirname(os.path.abspath(__file__))+os.sep+"data"+os.sep+filename
        if os.path.exists(default):
            self.load(default)

    def download(self):
        if not self.URL:
            return None
        url = urllib2.urlopen(self.URL)
        data = url.read()
        url.close()
        if self.URL.lower().endswith(".pdf"):
            suf = ".pdf"
        elif self.URL.lower().endswith(".xls"):
            suf = ".xls"
        elif self.URL.lower().endswith(".zip"):
            suf = ".zip"
        else:
            suf = ".txt"
        tfname = tempfile.mkstemp(suffix=suf)[1]
        tfile = open(tfname,"wb")
        tfile.write(data)
        tfile.close()
        if suf == ".pdf":
            os.system("pdftotext "+tfname)
            return tfname[:-4]+".txt"
        elif suf == ".zip":
            zfile = zipfile.ZipFile(tfname)
            for name in zfile.namelist:
                if "Custo" in name:
                    data = zfile.read(name)
                    pfile = open(tfname[:-4]+".pdf","wb")
                    pfile.write(data)
                    pfile.close()
                    os.system("pdftotext "+tfname[:-4]+".pdf")
                    return tfname[:-4]+".txt"
        else:
            return tfname

    def search(self,pattern,cub=None):
        def cleanstring(inputstr):
            if not isinstance(inputstr,unicode):
                inputstr = inputstr.decode("utf8")
            nfkd_form = unicodedata.normalize('NFKD', inputstr)
            cleanstr = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
            return cleanstr.upper()
        if not self.codes:
            return None
        pattern = pattern.split(" ")
        results = []
        for i in range(len(self.codes)):
            ok = None
            for pat in pattern:
                anyok = False
                for orpat in pat.split("|"):
                    if cleanstring(orpat) in cleanstring(self.descriptions[i]):
                        anyok = True
                if anyok:
                    if ok in [None,True]:
                        ok = True
                else:
                    ok = False
            if ok:
                results.append([self.codes[i],self.descriptions[i],self.indexize(self.values[i],cub),self.units[i]])
        return results

    def getcode(self,pattern,cub=None):
        def cleancode(code):
            res = ""
            for char in code:
                if char.isdigit():
                    res += char
            return res
        results = []
        pattern = cleancode(pattern)
        for i in range(len(self.codes)):
            if pattern in cleancode(self.codes[i]):
                results.append([self.codes[i],self.descriptions[i],self.indexize(self.values[i],cub),self.units[i]])
        return results

    def indexize(self,value,cub=None):
        if cub and self.CUB:
            fact = cub/self.CUB
            return value*fact
        else:
            return value


class source_fde(source):

    """Secretaria de Educação do Estado de São Paulo"""

    def __init__(self):
        source.__init__(self)
        self.Name = "FDE-SP"
        self.Description = "Secretaria da Educação do Estado de São Paulo"
        self.URL = "http://arquivo.fde.sp.gov.br/fde.portal/PermanentFile/File/TAB_SINT_ABR_16.pdf"
        self.City = "São Paulo"
        self.Country = "Brazil"
        self.Month = 07
        self.Year = 2016
        self.refURL = "http://www.fde.sp.gov.br/PagePublic/Interna.aspx?codigoMenu=189"
        self.Currency = "BRL"
        self.defaultfile = "fde-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv"
        self.loaddefault(self.defaultfile)
        self.CUB = 1292.18

    def build(self):
        tf = None
        tf = os.path.dirname(os.path.abspath(__file__))+os.sep+"sources"+os.sep+"fde.txt"
        if not tf:
            defaultlocation = os.path.dirname(os.path.abspath(__file__))+os.sep+"sources"+os.sep+"fde.pdf"
            if os.path.exists(defaultlocation):
                print "building from ",defaultlocation
                tf = defaultlocation
                os.system("pdftotext "+tf)
                tf = tf[:-4]+".txt"
            else:
                tf = self.download()
        if not tf:
            return
        f = open(tf,"rb")
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []
        datatype = ""
        skipstart = ["relat\xc3\x93rio","tabela","data","ls","descrição","bdi","unidade","página","valor"]
        skipstartexcept=["TABELA DE BASQUETE COM ARO E CESTO"]
        skipall = ["serviço"]
        doubles = ["FUNDAÇÃO-ESTACA-TUBULÃO","DIREÇOES","PILARES","FORNEC. E INST.","OU IGUAL 60CM","IGUAL 1,50X1,50","(MANUAL)","INCLINADAS 39X39X10CM",
                   "REVESTIMENTOS","ENTARUGAMENTO","L=101CM","AMERICANA-GRANITO","SOBREPOR","FECHADURAS SOBREPOR","DE FERRO POLIDO","FERRO","48%","INSTALADO",
                   "PINTURA ESMALTE","ESMALTE","PINTURA ESMALTE","COM PINTURA ESMALTE","H=260MM","H=180MM","FACES COM PINT FACES APARENTES.","INF PLANO COM PINT FACES APARENT",
                   "INF PLANO COM PINT FACES APARENTE","PADRAO CRECHE","CRECHE","NATURAL E=0,80MM PERFIL 700/800","E=0,80MM COM TAMPÃO","BARRO SOBRE LAJE","VAO LIVRE",
                   "FIBRO-CIM SOBRE LAJE","BARRO/FIBRO-CIM/AL/PLAST/PLANA PRE-FAB","S/REAPROV","PARAFUSOS","32MM 1 1/4\"","40MM 1 1/2\"","PARTICIPANTE)","FECHO ROTATIVO.",
                   "INCL.FIX.NA PAREDE","FORNECIDO E INSTALADO","AUTOMATICO","COMBUST.NBR 15526/07","P/MANGUEIRA","KVA","PARA CALÇADA AES ELETROPAULO","PARA CALÇADA - CPFL, EDP BA",
                   "ELETROP/BANDEIRANTE/CPFL/ELEKTRO","V):BANDEIRANTE/CPFL/ELEKTRO","ELETROP/BANDEIRANTE/ELEKTRO","QUENTE","GALV.A QUENTE","AMARELO.","25MM AMARELO.","25MM AMARELO",
                   "ELETROD.PVC RIGIDO","ELETROD.PVC RÍGIDO","RÍGIDO","LAMP.FLUORESC.COMPACTA (1X23W)","(2X32W)","(2x32W)","(4X16W)","(4x16W)","(2X28W)","(1X28W)","VAPOR SODIO 1X70W","FLUOR. 2X36W",
                   "TUBULAR DE VAPOR DE SÓDIO 1X150W.","TUBULAR DE VAPOR DE SÓDIO 1X250W.","INTERNA)","PASSAGEM","B.T","RECALQUE","FLUORESC","PENDENTES","OLHAL","A.T.","INTERNA)",
                   "PERFILADO","LAG","INCANDESC","FLUORESC","FACHADA","TIPO OLHAL","A.T","P/BARRAM.COBRE A.T","VARA/ESTRIBO FRONTAL","PRESSAO P/CABOS","PERFILADOS","JARDINS",
                   "FLUORESCENTES","P.RAIOS","DE COBRE NU","ESTALEIRO","COMPLETO","BL.BT","QD.COMANDO BOMBA RECALQUE","(IL-44)","(IL-45)","SOQUETES (IL-62)","P/SUSTENTAÇÃO DE FORRO PVC",
                   "EST","QUADRO","CERÂMICOS","EXPANDIDA","ASSENTAMENTO","C/ARGAMASSA","ACUSTICA","COEF.ATRITO MINIMO 0,4 USO EXCLUSIVO","7CM","EXCLUSIVO PADRAO CRECHE","17CM)","BASE",
                   "ARG ASSENT.","BAGUETES","ESTRUTURA DE MADEIRA","APARENTE","MADEIRA","C/LIXAMENTO","QUIMICO","C/PROD.QUIMICO","MASSA","ZARCAO","H=185CM/SAPAT","H=185CM/BROCA","H=235CM/SAPATA",
                   "H=235CM/BROCA","GROSSA","LASTRO DE BRITA","TOPO DA COPA.","ALTURA SUPERIOR A 10M ","INSPEÇÃO Ø 0,60M","P/CHUVEIRO,INCLUSIVE SUPORTE AR COND.","MICTÓRIO E 4 PONTOS CHUV.",
                   "NATURAL OU GELADA.","10000 BTU.","INCLUSIVE MONTAGEM E FRETE.","LOGOTIPO","E COMBUST USO EXCLUS UNID.MÓVEL","AJUDANTES.","OBRA","PROJ.REF.1201040-PD.ÍNDIO","INCLUSO COLETA DE EFLUENTES",
                   "EFLUENTES","BRAILLE","(INCL.CONEX.E FIXAÇOES EM POSTE)","NBR 13897","LOGOTIPO","SOLVENTE","MONOCOMPONENTE","ADENSADO","7CM","M3X","TRAÇO 1:4 ESPESSURA 3CM",
                   "APLICAÇAO 4 DEMÃOS INCLUS.TELA ESTRUTURAN","ACRILICO BASE SOLVENTE","DEMÃOS SEMIFLEXIVEL + 4 DEMÃOS FL","COM APLICAÇÃO 4 DEMÃOS","ALTURA SUPERIOR A 10M",
                   "TRANSPLANTE INTERNO DE ÁRVORE COM 30CM<DAP<45CM APLICAVEL","EXCLUSIVAMENTE PELA GOE/DOEV UMA UNIDADE-D","TRIAGEM (ATT)"]
        pairs = [["QE-12 QUADRA DE ESPORTES/PISO DE CONCRETO ARMADO/FUNDACAO DIRET-600","M2"]]
        ln = 0
        for l in f:
            ln += 1
            l = l.strip()

            # skip lines
            skip = False
            if datatype == "skip":
                datatype = "description"
                skip = True
            if not l:
                skip = True
            for s in skipstart:
                if l.lower().startswith(s):
                    if not l in skipstartexcept:
                        #print "found line starting with ",s," : ",l
                        skip = True
                        break
            if not skip:
                for s in skipall:
                    if l.lower() == s:
                        skip = True
                        break
            if skip:
                continue

            # distribute lines according to type
            sk = False
            for p in pairs:
                if l == p[0]:
                    datatype = "description"
                    self.descriptions.append(l+" "+p[1])
                    datatype = "skip"
                    sk = True
                    break
            if sk:
                continue
            if l in doubles:
                datatype = "description"
                self.descriptions[-1] = self.descriptions[-1]+" "+l
                continue
            if len(l.split(".")) == 3:
                a = l.split(".")
                if a[0].isdigit() and a[1].isdigit() and a[2].isdigit():
                    datatype = "code"
                    self.codes.append(l)
                    continue
            if len(l.split(",")) == 2:
                a = l.split(",")
                if a[0].isdigit() and a[1].isdigit():
                    datatype = "value"
                    self.values.append(float(l.replace(",",".")))
                    continue
            if (len(l) <= 2):
                if not(l[0].isdigit()):
                    datatype = "unit"
                    self.units.append(l)
                    continue
            if (len(l) >= 3):
                if not(l[0].isdigit()) or (l[1] == " "):
                    datatype = "description"
                    self.descriptions.append(l)
                    continue
            print "unparsed line: (",ln,") ",l
        f.close()
        print "parsed data: ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)


class source_pmsp(source):

    """Prefeitura municipal de São Paulo"""

    def __init__(self):
        source.__init__(self)
        self.Name = "PMSP"
        self.Description = "Prefeitura de São Paulo"
        self.URL = "http://www.prefeitura.sp.gov.br/cidade/secretarias/upload/infraestrutura/tabelas_de_custos/arquivos/2016%20Jan/SEM%20DESONERA%C3%87%C3%82O/EDIF/Comp%20Custos%20Unit%20EDIF%20SEM%20Des%20JAN%202016(1).xls"
        self.City = "São Paulo"
        self.Country = "Brazil"
        self.Month = 01
        self.Year = 2016
        self.refURL = "http://www.prefeitura.sp.gov.br/cidade/secretarias/infraestrutura/tabelas_de_custos/index.php?p=215107"
        self.Currency = "BRL"
        self.defaultfile = "pmsp-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv"
        self.loaddefault(self.defaultfile)
        self.CUB = 1232.14

    def build(self):
        import xlrd
        tf = self.download()
        if not tf:
            return
        f = xlrd.open_workbook(tf)
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []
        sh = f.sheets()[0]
        for i in range(1,sh.nrows):
            r = sh.row(i)
            if (r[0].ctype == xlrd.XL_CELL_NUMBER) and (r[1].ctype == xlrd.XL_CELL_TEXT) and (r[7].ctype == xlrd.XL_CELL_TEXT) and (r[9].ctype == xlrd.XL_CELL_NUMBER):
                c = str(int(r[0].value))
                cs = c[0:2]+"."+c[2:4]+"."
                if len(c[4:]) == 1:
                    cs += "0"+c[4:]
                else:
                    cs += c[4:]
                self.codes.append(cs)
                self.descriptions.append(r[1].value)
                self.units.append(r[7].value)
                self.values.append(r[9].value)
        #f.close()
        print "parsed data: ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)


class source_sinapi(source):

    """Caixa Federal - Estado de São Paulo"""

    def __init__(self):
        source.__init__(self)
        self.Name = "SINAPI-SP"
        self.Description = "Caixa Federal - Estado de São Paulo"
        self.URL = "http://www.caixa.gov.br/Downloads/sinapi-a-partir-jul-2014-sp/SINAPI_ref_Insumos_Composicoes_SP_062016_NaoDesonerado.zip"
        self.City = "São Paulo"
        self.Country = "Brazil"
        self.Month = 07
        self.Year = 2016
        self.refURL = "https://sinapiexcel.wordpress.com/"
        self.Currency = "BRL"
        self.defaultfile = "sinapi-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv"
        self.loaddefault(self.defaultfile)
        self.CUB = 1292.18

    def build(self):
        import openpyxl
        tf = None
        if not tf:
            defaultlocation = os.path.dirname(os.path.abspath(__file__))+os.sep+"sources"+os.sep+"sinapi.xlsx"
            if os.path.exists(defaultlocation):
                print "building from ",defaultlocation
                tf = defaultlocation
            else:
                tf = self.download()
        if not tf:
            return
        f = openpyxl.load_workbook(tf)
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []
        sh = f.get_sheet_by_name(f.get_sheet_names()[0])
        for i in range(1,sh.max_row):
            r = sh.rows[i]
            self.codes.append(r[0].value)
            self.descriptions.append(r[1].value)
            self.units.append(r[2].value)
            self.values.append(r[3].value)
        print "parsed data: ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)


class source_seinfra_ce(source):

    """Secretaria de Infraestutura do Ceará"""

    def __init__(self):
        source.__init__(self)
        self.Name = "SEINFRA-CE"
        self.Description = "Secretaria de Infraestutura do Ceará"
        self.URL = "http://www.seinfra.ce.gov.br/siproce/onerada/Tabela-de-Insumos-024.xls?a=1463159682253"
        self.City = "Fortaleza"
        self.Country = "Brazil"
        self.Month = 03
        self.Year = 2016
        self.refURL = "http://www.seinfra.ce.gov.br/index.php/tabela-de-custos-unificada"
        self.Currency = "BRL"
        self.defaultfile = "seinfra-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv"
        self.loaddefault(self.defaultfile)
        self.CUB = 1064.12

    def build(self):
        import xlrd
        tf = None
        if not tf:
            defaultlocation = os.path.dirname(os.path.abspath(__file__))+os.sep+"sources"+os.sep+"seinfra.xls"
            if os.path.exists(defaultlocation):
                print "building from ",defaultlocation
                tf = defaultlocation
            else:
                tf = self.download()
        if not tf:
            return
        f = xlrd.open_workbook(tf)
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []
        sh = f.sheets()[0]
        for i in range(5,sh.nrows):
            r = sh.row(i)
            if (r[0].ctype == xlrd.XL_CELL_TEXT) and (r[1].ctype == xlrd.XL_CELL_TEXT) and (r[4].ctype == xlrd.XL_CELL_TEXT) and (r[5].ctype == xlrd.XL_CELL_NUMBER):
                self.codes.append(r[0].value)
                self.descriptions.append(r[1].value)
                self.units.append(r[4].value)
                self.values.append(r[5].value)
        #f.close()
        print "parsed data: ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)



sources = [source_fde(),source_pmsp(),source_sinapi(),source_seinfra_ce()]


def tabulate(orig, cod, descr, val, unit):

    """prints the 5 pieces of data in a table"""

    col1 = 12
    col2 = 12
    try:
        rows, columns = os.popen('stty size', 'r').read().split()
        col3 = int(columns) - 37
    except:
        col3 = 72
    col4 = 10

    print ""
    cod = str(cod)
    val = str(val)
    orig = orig.split(" ")[0]
    orig = orig[:col1-2] + (col1-len(orig[:col1-2]))*" "
    cod = cod + (col2-len(cod))*" "
    val = val + (col4-len(val))*" "
    d = []
    line = ""
    for word in descr.split(" "):
        if len(line)+len(word) > col3-2:
            d.append(line)
            line = word
        else:
            if line:
                line += " " + word
            else:
                line = word
    if line:
        d.append(line)
    fd = d[0] + (col3-len(unicode(d[0].decode("utf8"))))*" "
    print orig+cod+fd+val+unit
    for l in d[1:]:
        print (col1+col2)*" "+l


def search(pattern,location=None,sourcenames=[],code=False,prn=False,cub=None):

    """search(pattern,[location|sourcenames|code|prn|cub]): searches sources for a given 
    pattern in descriptions.

    Prints a list of found entries. Separating search terms with a space (ex. brick wall 14cm)
    will return only items that have all the terms. Separating terms with a pipe
    (ex. brick|concrete wall) will return any item that has one or the other term. If
    location is given, only the sources that match the location (either country or city) will
    be searched.If a list of source names are given, only those sources are searched.
    
    If prn = True, the results are printed on screen and nothing is returned.
    
    If cub is a float value, prices will be converted according to the given CUB
    value (Custos básicos da construção civil / R8-N sem desoneração)"""

    #print "searching for :",pattern," sources: ",sourcenames," location: ",location

    if not isinstance(sourcenames,list):
        if sourcenames == None:
            sourcenames = []
        else:
            sourcenames = [sourcenames]
    if isinstance(pattern,list):
        pattern = " ".join(pattern)
    if prn:
        tabulate("Origin","Code","Description","Price","Unit")
    res = []
    for source in sources:
        if ( not location and not sourcenames ) \
        or ( location and ( (source.Country == location) or (source.City == location) ) ) \
        or ( sourcenames and (source.Name in sourcenames) ):
            if code:
                results = source.getcode(pattern,cub)
            else:
                results = source.search(pattern,cub)
            if results:
                if prn:
                    for result in results:
                        tabulate(source.Name,*result)
                else:
                    res.append([source,results])
    if not prn:
        return res


if __name__ == "__main__":
    # running directly from command line
    helpmsg = __doc__+"""

    Usage: priceapi.py [OPTIONS] searchterm1|alternativeterm1 searchterm2 ...

    Separate search term by a space to retrieve only entries that contain all
    the search terms. Use a | character to separate alternative search term
    (entries containing one OR the other will be retrieved).

    Options: --location=XXX: Specify a city or country name to limit the search to.
             --source=XXX  : Specify a source name or comma-separated list of
                             source names to limit the search to.
             --code=XXX    : Searches for a specific code. Dots and hyphens are
                             ignored.
             --cub=XXXX    : Gives a specific CUB value to convert values to
    """
    
    for s in sources:
        print "Loaded",s.Name+(11-len(s.Name))*" ","(",str(s.Month).zfill(2),"/",s.Year,")",s.Currency,":",len(s.codes),"/",len(s.descriptions),"/",len(s.values),"/",len(s.units)," - CUB:",s.CUB
    print

    if len(sys.argv) == 1:
        # if no argument is given, print help text
        print helpmsg
    else:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ["location=","source=","code=","cub="])
        except getopt.GetoptError:
            print helpmsg
            sys.exit()
        else:
            location=None
            sourcenames=[]
            code=None
            cub=None
            for o, a in opts:
                if o == "--location":
                    location = a
                elif o == "--source":
                    sourcenames = a.split(",")
                elif o == "--code":
                    args = a
                    code = True
                elif o == "--cub":
                    try:
                        cub = float(a)
                    except:
                        print helpmsg
                        print "Error - cub must be a float value"
                        sys.exit()
            search(args,location,sourcenames,code,prn=True,cub=cub)




