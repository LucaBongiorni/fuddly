################################################################################
#
#  Copyright 2014-2016 Eric Lacombe <eric.lacombe@security-labs.org>
#
################################################################################
#
#  This file is part of fuddly.
#
#  fuddly is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  fuddly is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with fuddly. If not, see <http://www.gnu.org/licenses/>
#
################################################################################

from framework.data_model import *
from framework.data_model_helpers import *
from framework.value_types import *

markers = {
    'SOF': {0: 0xFFC0,
            1: 0xFFC1,
            2: 0xFFC2,
            3: 0xFFC3},
    'DHT': 0xFFC4,
    'DAC': 0xFFCC,
    'SOI': 0xFFD8,
    'SOE': 0xFFD9,
    'SOS': 0xFFDA,
    'DQT': 0xFFDB,
    'DNL': 0xFFDC,
    'JFIF': 0xFFE0,
    'EXIF': 0xFFE1,
    'COM': 0xFFFE,
    }


class JPG_DataModel(DataModel):

    file_extension = 'jpg'
    name = 'jpg'

    def absorb(self, data, idx):
        nm = 'jpg_{:0>2d}'.format(idx)
        jpg = self.jpg.get_clone(nm, new_env=True)
        jpg.set_current_conf('ABS', recursive=True)
        status, off, size, name = jpg.absorb(data, constraints=AbsNoCsts(size=True, struct=True,
                                                                         contents=True))

        print('{:s} Absorb Status: {!r}, {:d}, {:d}, {:s}'.format(nm, status, off, size, name))
        print(' \_ length of original jpg: {:d}'.format(len(data)))
        print(' \_ remaining: {!r}'.format(data[size:size+1000]))

        if status == AbsorbStatus.FullyAbsorbed:
            x = jpg['.*/SOF_hdr/X'].get_raw_value()
            y = jpg['.*/SOF_hdr/Y'].get_raw_value()
            d_priv = {'height':y, 'width':x}
            jpg.set_private(d_priv)
            print("--> Create {:s} from provided JPG sample [x:{:d}, y:{:d}].".format(nm, x, y))
            return jpg
        else:
            return Node(nm, values=['JPG ABSORBSION FAILED'])

    def build_data_model(self):

        jpg_desc = \
        {'name': 'jpg',
         'contents': [
             {'name': 'SOF_hdr',
              'contents': [
                  {'name': 'before_SOF',
                   'contents': String(size=0),
                   'absorb_csts': AbsNoCsts(),
                   'set_attrs': MH.Attr.Abs_Postpone,  # Only works if it is side-by-side with the
                                                       # the node that will provide the constraint
                   'mutable': False},

                  {'name': 'F_marker',
                   'contents': UINT16_be(int_list=[m for m in markers['SOF'].values()])},
                  {'name': 'Lf',
                   'contents': MH.LEN(vt=UINT16_be, base_len=8),
                   'node_args': 'F_CompGroup',
                   'alt': [
                       {'conf': 'ABS',
                        'contents': UINT16_be()}
                   ]},
                  {'name': 'P',
                   'contents': UINT8(int_list=[8,12])},
                  {'name': 'Y',
                   'contents': UINT16_be(maxi=65535)},
                  {'name': 'X',
                   'contents': UINT16_be(mini=1, maxi=65535)},
                  {'name': 'Nf',
                   'contents': MH.QTY(node_name='F_Comp', vt=UINT8),
                   'node_args': 'F_CompGroup',
                   'alt': [
                       {'conf': 'ABS',
                        'contents': UINT8(mini=1, maxi=255)},
                   ]},
                  {'name': 'F_CompGroup',
                   'custo_clear': MH.Custo.NTerm.MutableClone,
                   'contents': [
                       {'name': 'F_Comp',
                        'qty': (1, 255),
                        'contents': [
                           {'name': 'Cf',
                            'contents': UINT8(mini=0, maxi=255)},
                           {'name': 'H&V',
                            'contents': BitField(subfield_sizes=[4,4], endian=VT.BigEndian,
                                                 subfield_val_extremums=[[1,4], [1,4]],
                                                 subfield_descs=['H sampling', 'V sampling'])},
                           {'name': 'Tq',
                            'contents': UINT8(mini=0, maxi=3)},
                       ]}
                   ]},
              ]},

             {'name': 'SOS_hdr',
              'contents': [
                  {'name': 'between_SOF_SOS',
                   'contents': String(),
                   'random': True,
                   'absorb_csts': AbsNoCsts(),
                   'set_attrs': MH.Attr.Abs_Postpone,
                   'mutable': False},

                  {'name': 'S_marker',
                   'contents': UINT16_be(int_list=[markers['SOS']])},
                  {'name': 'Ls',
                   'contents': MH.LEN(vt=UINT16_be, base_len=6),
                   'node_args': 'S_CompGroup',
                   'alt': [
                       {'conf': 'ABS',
                        'contents': UINT16_be()}
                   ]},
                  {'name': 'Ns',
                   'contents': MH.QTY(node_name='S_Comp', vt=UINT8),
                   'node_args': 'S_CompGroup',
                   'alt': [
                       {'conf': 'ABS',
                        'contents': UINT8(mini=1, maxi=255)},
                   ]},
                  {'name': 'S_CompGroup',
                   'custo_clear': MH.Custo.NTerm.MutableClone,
                   'contents': [
                       {'name': 'S_Comp',
                        'qty': (1, 4),
                        'contents': [
                            {'name': 'Cs',
                             'contents': UINT8()},
                            {'name': 'Td&Ta',
                             'contents': BitField(subfield_sizes=[4, 4], endian=VT.BigEndian,
                                                  subfield_val_extremums=[[0, 3], [0, 3]],
                                                  subfield_descs=['DC entropy', 'AC entropy'])},
                        ]}
                   ]},
                  {'name': 'Ss',
                   'contents': UINT8(mini=0, maxi=63)},
                  {'name': 'Se',
                   'contents': UINT8(mini=0, maxi=63)},
                  {'name': 'Ah&Al',
                   'contents': BitField(subfield_sizes=[4, 4], endian=VT.BigEndian,
                                        subfield_val_extremums=[[0, 13], [0, 13]],
                                        subfield_descs=['approx high', 'approx low'])},
              ]},

             {'name': 'afterSOS',
              'mutable': False,
              'contents': String(min_sz=0),
              'absorb_csts': AbsNoCsts()}
         ]}

        mh = ModelHelper(delayed_jobs=True)
        self.jpg = mh.create_graph_from_desc(jpg_desc)

        self.jpg_dict = self.import_file_contents(extension='jpg')
        self.register(self.jpg, *self.jpg_dict.values())


data_model = JPG_DataModel()

