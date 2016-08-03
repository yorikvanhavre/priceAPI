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

__title__  = "Price API"
__author__ = "Yorik van Havre"
__url__    = "http://yorik.uncreated.net"

import os,urllib2,tempfile,csv,xlrd,zipfile,openpyxl


class source:

    """Base class for price sources"""

    def __init__(self):
        self.URL = None
        self.Name = None
        self.City = None
        self.Country = None
        self.Month = None
        self.Year = None
        self.refURL = None
        self.Data = None
        self.Currency = None
        self.descriptions = []
        self.values = []
        self.units = []
        self.codes = []

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

    def save(self,filename):
        if self.codes:
            with open(filename, 'wb') as csvfile:
                csvfile = csv.writer(csvfile)
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
                    csvfile.writerow([self.codes[i],d,self.values[i],u])

    def load(self,filename):
        with open(filename, 'rb') as csvfile:
            csvfile = csv.reader(csvfile)
            self.descriptions = []
            self.values = []
            self.units = []
            self.codes = []
            for row in csvfile:
                self.codes.append(row[0])
                self.descriptions.append(row[1])
                self.values.append(row[2])
                self.units.append(row[3])
        print "Loaded",self.Name,"(",str(self.Month).zfill(2),"/",self.Year,") /",self.Currency,": ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)

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
            
    def search(self,pattern):
        if not self.codes:
            return None
        pattern = pattern.split(" ")
        results = []
        for i in range(len(self.codes)):
            ok = None
            for pat in pattern:
                if pat.upper() in self.descriptions[i].upper():
                    if ok in [None,True]:
                        ok = True
                else:
                    ok = False
            if ok:
                results.append([self.codes[i],self.descriptions[i],self.values[i],self.units[i]])
        return results


class source_fde(source):
    
    """Secretaria de Educação do Estado de São Paulo"""
    
    def __init__(self):
        source.__init__(self)
        self.Name = "FDE São Paulo"
        self.URL = "http://arquivo.fde.sp.gov.br/fde.portal/PermanentFile/File/TAB_SINT_ABR_16.pdf"
        self.City = "São Paulo"
        self.Country = "Brazil"
        self.Month = 04
        self.Year = 2016
        self.refURL = "http://www.fde.sp.gov.br/PagePublic/Interna.aspx?codigoMenu=189"
        self.Currency = "BRL"
        self.loaddefault("fde-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv")

    def build(self):
        tf = self.download()
        if not tf:
            return
        with open(tf,"rb") as f:
            self.descriptions = []
            self.values = []
            self.units = []
            self.codes = []
            datatype = ""
            skipstart = ["relat\xc3\x93rio","tabela","data","ls","descrição","bdi","unidade","página","valor"]
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
                       "EFLUENTES","BRAILLE","(INCL.CONEX.E FIXAÇOES EM POSTE)","NBR 13897","LOGOTIPO","SOLVENTE","MONOCOMPONENTE","ADENSADO","7CM","M3X"]
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

        print "parsed data: ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)


class source_pmsp(source):
    
    """Prefeitura municipal de São Paulo"""
    
    def __init__(self):
        source.__init__(self)
        self.Name = "Prefeitura de São Paulo"
        self.URL = "http://www.prefeitura.sp.gov.br/cidade/secretarias/upload/infraestrutura/tabelas_de_custos/arquivos/2016%20Jan/SEM%20DESONERA%C3%87%C3%82O/EDIF/Comp%20Custos%20Unit%20EDIF%20SEM%20Des%20JAN%202016(1).xls"
        self.City = "São Paulo"
        self.Country = "Brazil"
        self.Month = 01
        self.Year = 2016
        self.refURL = "http://www.prefeitura.sp.gov.br/cidade/secretarias/infraestrutura/tabelas_de_custos/index.php?p=215107"
        self.Currency = "BRL"
        self.loaddefault("pmsp-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv")
        
    def build(self):
        tf = self.download()
        if not tf:
            return
        with xlrd.open_workbook(tf) as f:
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
        print "parsed data: ",len(self.codes),"/",len(self.descriptions),"/",len(self.values),"/",len(self.units)


class source_sinapi(source):
    
    """SINAPI - Caixa Federal"""
    
    def __init__(self):
        source.__init__(self)
        self.Name = "Caixa Federal (SINAPI)"
        self.URL = "http://www.caixa.gov.br/Downloads/sinapi-a-partir-jul-2014-sp/SINAPI_ref_Insumos_Composicoes_SP_062016_NaoDesonerado.zip"
        self.City = "São Paulo"
        self.Country = "Brazil"
        self.Month = 06
        self.Year = 2016
        self.refURL = "https://sinapiexcel.wordpress.com/"
        self.Currency = "BRL"
        self.loaddefault("sinapi-"+str(self.Year)+"."+str(self.Month).zfill(2)+".csv")
        
    def build(self):
        #tf = self.download()
        #if not tf:
        #    return
        tf = "examples/sinapi.xlsx"
        f =  openpyxl.load_workbook(tf)
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


sources = [source_fde(),source_pmsp(),source_sinapi()]


def tabulate(orig, cod, descr, val, unit):
    cod = str(cod)
    val = str(val)
    orig = orig.split(" ")[0]
    orig = orig[:6] + (8-len(orig[:6]))*" "
    cod = cod + (12-len(cod))*" "
    val = val + (10-len(val))*" "
    d = []
    line = ""
    for word in descr.split(" "):
        if len(line)+len(word) > 75:
            d.append(line)
            line = word
        else:
            if line:
                line += " " + word
            else:
                line = word
    if line:
        d.append(line)
    fd = d[0] + (80-len(unicode(d[0].decode("utf8"))))*" "
    print orig+cod+fd+val+unit
    for l in d[1:]:
        print 20*" "+l


def search(pattern):

    print ""
    tabulate("Origin","Code","Description","Price","Unit")
    print ""
    for source in sources:
        results = source.search(pattern)
        if results:
            for result in results:
                tabulate(source.Name,*result)
                print ""





