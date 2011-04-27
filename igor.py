# This program is in the public domain
"""
IGOR file reader.

igor.load('filename') or igor.loads('data') loads the content of an igore file
into memory as a folder structure.

Returns the root folder.

Folders have name, path and children.
Children can be indexed by folder[i] or by folder['name'].
To see the whole tree, use: print folder.format()

The usual igor folder types are given in the technical reports
PTN003.ifn and TN003.ifn.
"""
__version__="0.8"

import struct
import numpy

NUMTYPE = {
     1: numpy.complex64,
     2: numpy.float32,
     3: numpy.complex64,
     4: numpy.float64,
     5: numpy.complex128,
     8: numpy.int8,
    16: numpy.int16,
    32: numpy.int32,
 64+ 8: numpy.uint8,
 64+16: numpy.uint16,
 64+32: numpy.uint32,
}

ORDER_NUMTYPE = {
     1: 'c8',
     2: 'f4',
     3: 'c8',
     4: 'f8',
     5: 'c16',
     8: 'i1',
    16: 'i2',
    32: 'i4',
 64+ 8: 'u2',
 64+16: 'u2',
 64+32: 'u4',
}



class Formula(object):
    def __init__(self, formula, value):
	self.formula = formula
        self.value = value

class Variables(object): 
    """
    Contains system numeric variables (e.g., K0) and user numeric and string variables.
    """
    def __init__(self, data, order):
        version, = struct.unpack(order+"h",data[:2])
        if version == 1:
            pos = 8
            nSysVar, nUserVar, nUserStr \
                = struct.unpack(order+"hhh",data[2:pos])
            nDepVar, nDepStr = 0, 0
        elif version == 2:
            pos = 12
            nSysVar, nUservar, nUserStr, nDepVar, nDepStr \
                = struct.unpack(order+"hhh",data[2:pos])
        else:
            raise ValueError("Unknown variable record version "+str(version))
        self.sysvar, pos = _parse_sys_numeric(nSysVar, order, data, pos)
        self.uservar, pos = _parse_user_numeric(nUserVar, order, data, pos) 
        if version == 1:
            self.userstr, pos = _parse_user_string1(nUserStr, order, data, pos) 
        else:
            self.userstr, pos = _parse_user_string2(nUserStr, order, data, pos) 
        self.depvar, pos = _parse_dep_numeric(nDepVar, order, data, pos) 
        self.depstr, pos = _parse_dep_string(nDepStr, order, data, pos)
    def format(self, indent=0):
        return " "*indent+"<Variables: system %d, user %d, dependent %s>"\
            %(len(self.sysvar),
              len(self.uservar)+len(self.userstr),
              len(self.depvar)+len(self.depstr))

class History(object):
    """
    Contains the experiment's history as plain text.
    """
    def __init__(self, data, order): self.data = data
    def format(self, indent=0):
        return " "*indent+"<History>"

class Wave(object):
    """
    Contains the data for a wave
    """
    def __init__(self, data, order):
        version, = struct.unpack(order+'h',data[:2])
        if version == 1:
            pos = 8
            extra_offset,checksum = struct.unpack(order+'ih',data[2:pos])
            formula_size = note_size = pic_size = 0
        elif version == 2:
            pos = 16
            extra_offset,note_size,pic_size,checksum \
                = struct.unpack(order+'iiih',data[2:pos])
            formula_size = 0
        elif version == 3:
            pos = 20
            extra_offset,note_size,formula_size,pic_size,checksum \
                = struct.unpack(order+'iiiih',data[2:pos])
        elif version == 5:
            checksum,extra_offset,formula_size,note_size, \
                = struct.unpack(order+'hiii',data[2:16])
            Esize = struct.unpack(order+'iiiiiiiii',data[16:52])
            textindsize, = struct.unpack('i',data[52:56])
            picsize = 0
            pos = 64
        else:
            raise ValueError("unknown wave version "+str(version))
        extra_offset += pos

        if version in (1,2,3):
            type, = struct.unpack(order+'h',data[pos:pos+2])
            name = data[pos+6:data.find(chr(0),pos+6,pos+26)]
            #print "name3",name,type
            data_units = data[pos+34:data.find(chr(0),pos+34,pos+38)]
            xaxis = data[pos+38:data.find(chr(0),pos+38,pos+42)]
            points, = struct.unpack(order+'i',data[pos+42:pos+46])
            hsA,hsB = struct.unpack(order+'dd',data[pos+48:pos+64])
            fsValid,fsTop,fsBottom \
                = struct.unpack(order+'hdd',data[pos+70:pos+88])
            created,_,modified = struct.unpack(order+'IhI',data[pos+98:pos+108])
            pos += 110
            dims = (points,0,0,0)
            sf = (hsA,0,0,0,hsB,0,0,0)
            axis_units = (xaxis,"","","")
        else: # version is 5
            created,modified,points,type \
                = struct.unpack(order+'IIih',data[pos+4:pos+18])
            name = data[pos+28:data.find(chr(0),pos+28,pos+60)]
            #print "name5",name,type
            dims = struct.unpack(order+'iiii',data[pos+68:pos+84])
            sf = struct.unpack(order+'dddddddd',data[pos+84:pos+148])
            data_units = data[pos+148:data.find(chr(0),pos+148,pos+152)]
            axis_units = tuple(data[pos+152+4*i 
                                 : data.find(chr(0),pos+152+4*i,pos+156+4*i)]
                         for i in range(4))
            fsValid,_,fsTop,fsBottom \
                = struct.unpack(order+'hhdd',data[pos+172:pos+192])
            pos += 320

        if type == 0:
            text = data[pos:extra_offset]
            textind = numpy.fromstring(data[-textindsize:], order+'i')
            textind = numpy.hstack((0,textind))
            value = [text[textind[i]:textind[i+1]] 
                     for i in range(len(textind)-1)] 
        else:
            trimdims = tuple(d for d in dims if d)
            dtype = order+ORDER_NUMTYPE[type]
            size = int(dtype[2:])*numpy.prod(trimdims)
            value = numpy.fromstring(data[pos:pos+size],dtype)
            value = value.reshape(trimdims)

        pos = extra_offset
        formula = data[pos:pos+formula_size]
        pos += formula_size
        notes = data[pos:pos+note_size]
        pos += note_size
        if version == 5:
            offset = numpy.cumsum(numpy.hstack((pos,Esize)))
            Edata_units = data[offset[0]:offset[1]]
            Eaxis_units = [data[offset[i]:offset[i+1]] for i in range(1,5)]
            Eaxis_labels = [data[offset[i]:offset[i+1]] for i in range(5,9)]
            if Edata_units: data_units = Edata_units
            for i,u in enumerate(Eaxis_units):
                if u: axis_units[i] = u
            axis_labels = Eaxis_labels
            pos = offset[-1]

            
        self.name = name
        self.data = value
        self.data_units = data_units
        self.axis_units = axis_units
        self.fs,self.fstop,self.fsbottom = fsValid,fsTop,fsBottom
        self.axis = [numpy.linspace(a,b,n)
                     for a,b,n in zip(sf[:4],sf[4:],dims)]
        self.formula = formula
        self.notes = notes
    def format(self, indent=0):
        if isinstance(self.data, list):
            type,size = "text", "%d"%len(self.data)
        else:
            type,size = "data", "x".join(str(d) for d in self.data.shape)
        return " "*indent+"%s %s (%s)"%(self.name, type, size)
        
class Recreation(object):
    """
    Contains the experiment's recreation procedures as plain text.
    """
    def __init__(self, data, order): self.data = data
    def format(self, indent=0):
        return " "*indent + "<Recreation>"
class Procedure(object):
    """
    Contains the experiment's main procedure window text as plain text.
    """
    def __init__(self, data, order): self.data = data
    def format(self, indent=0):
        return " "*indent + "<Procedure>"
class GetHistory(object):
    """
    Not a real record but rather, a message to go back and read the history text.

    The reason for GetHistory is that IGOR runs Recreation when it loads the
    datafile.  This puts entries in the history that shouldn't be there.  The
    GetHistory entry simply says that the Recreation has run, and the History
    can be restored from the previously saved value.
    """
    def __init__(self, data, order): self.data = data
    def format(self, indent=0):
        return " "*indent + "<GetHistory>"
class PackedFile(object):
    """
    Contains the data for a procedure file or notebook in packed form.
    """
    def __init__(self, data, order): self.data = data
    def format(self, indent=0):
        return " "*indent + "<PackedFile>"
class Unknown(object):
    """
    Record type not documented in PTN003/TN003.
    """
    def __init__(self, data, order, type):
        self.data = data
        self.type = type
    def format(self, indent=0):
        return " "*indent + "<Unknown type %s>"%self.type

class _FolderStart(object):
    """
    Marks the start of a new data folder.
    """
    def __init__(self, data, order): 
        self.name = data[:data.find(chr(0))]
class _FolderEnd(object):
    """
    Marks the end of a data folder.
    """
    def __init__(self, data, order): self.data = data

class Folder(object):
    """
    Hierarchical record container.
    """
    def __init__(self, path):
        self.name = path[-1]
        self.path = path
        self.children = []
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.children[key]
        else:
            for r in self.children:
                if isinstance(r, (Folder,Wave)) and r.name == key:
                    return r
            raise KeyError("Folder %s does not exist"%key)
    def append(self, record):
        self.children.append(record)
    def format(self, indent=0):
        parent = " "*indent+self.name
        children = [r.format(indent=indent+2) for r in self.children]
        return "\n".join([parent]+children)

PARSER = {
1: Variables,
2: History,
3: Wave,
4: Recreation,
5: Procedure,
7: GetHistory,
8: PackedFile,
9: _FolderStart,
10: _FolderEnd,
}

def loads(s, ignore_unknown=True):
    """Load an igor file from string"""
    max = len(s)
    pos = 0
    ret = []
    stack = [Folder(path=['root'])]
    while pos < max:
        if pos+8 > max:
            raise IOError("invalid record header; bad pxp file?")
        ignore = ord(s[pos])&0x80
        order = '<' if ord(s[pos])&0x77 else '>'
        type, version, length = struct.unpack(order+'hhi',s[pos:pos+8])
        pos += 8
        if pos+length > len(s):
            raise IOError("final record too long; bad pxp file?")
        data = s[pos:pos+length]
        pos += length
        if not ignore:
            parse = PARSER.get(type, None)
            if parse:
                record = parse(data, order)
            elif ignore_unknown:
                continue
            else:
                record = Unknown(data=data, order=order, type=type)
            if isinstance(record, _FolderStart):
                 path = stack[-1].path+[record.name]
                 folder = Folder(path)
                 stack[-1].append(folder)
                 stack.append(folder)
            elif isinstance(record, _FolderEnd):
                 stack.pop()
            else:
                 stack[-1].append(record)
    if len(stack) != 1:
        raise IOError("FolderStart records do not match FolderEnd records")
    return stack[0]

def load(filename, ignore_unknown=True):
    """Load an igor file"""
    return loads(open(filename,'rb').read(),
                 ignore_unknown=ignore_unknown)

# ============== Variable parsing ==============
def _parse_sys_numeric(n, order, data, pos):
    values = numpy.fromstring(data[pos:pos+n*4], order+'f')
    pos += n*4
    var = dict(('K'+str(i),v) for i,v in enumerate(values)) 
    return var, pos

def _parse_user_numeric(n, order, data, pos):
    var = {}
    for i in range(n):
        name = data[pos:data.find(chr(0),pos,pos+32)]
        type,numtype,real,imag = struct.unpack(order+"hhdd",data[pos+32:pos+52])
        dtype = NUMTYPE[numtype]
        if dtype in (numpy.complex64, numpy.complex128):
            value = dtype(real+1j*imag)
        else:
            value = dtype(real) 
        var[name] = value
        pos += 56
    return var, pos

def _parse_dep_numeric(n, order, data, pos):
    var = {}
    for i in range(n):
        name = data[pos:data.find(chr(0),pos,pos+32)]
        type,numtype,real,imag = struct.unpack(order+"hhdd",data[pos+32:pos+52])
        dtype = NUMTYPE[numtype]
        if dtype in (numpy.complex64, numpy.complex128):
            value = dtype(real+1j*imag)
        else:
            value = dtype(real) 
        length, = struct.unpack(order+"h",data[pos+56:pos+58])
        var[name] = Formula(data[pos+58:pos+58+length-1], value)
        pos += 58+length
    return var, pos

def _parse_dep_string(n, order, data, pos):
    var = {}
    for i in range(n):
        name = data[pos:data.find(chr(0),pos,pos+32)]
        length, = struct.unpack(order+"h",data[pos+48:pos+50])
        var[name] = Formula(data[pos+50:pos+50+length-1], "")
        pos += 50+length
    return var, pos

def _parse_user_string1(n, order, data, pos):
    var = {}
    for i in range(n):
        name = data[pos:data.find(chr(0),pos,pos+32)]
        length, = struct.unpack(order+"h",data[pos+32:pos+34])
        value = data[pos+34:pos+34+length]
        pos += 34+length
        var[name] = value
    return var, pos

def _parse_user_string2(n, order, data, pos):
    var = {}
    for i in range(n):
        name = data[pos:data.find(chr(0),pos,pos+32)]
        length, = struct.unpack(order+"i",data[pos+32:pos+36])
        value = data[pos+36:pos+36+length]
        pos += 36+length
        var[name] = value
    return var, pos

