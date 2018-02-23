# XXX use MNE as data model for such things
# XXX MNE probably has such a parser anyway


class ElectrodeParser(object):

    def parse_asa_electrode_file(self, fname):
        "Parse an ASA electrode format file."
        contents = {'positions': [], 'labels': []}
        with open(fname, 'r') as fd:
            lines = (l for l in fd.readlines())
            # parse header
            for line in lines:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                if line.startswith('ReferenceLabel'):
                    contents['reference_label'] = parts[1]
                elif line.startswith('UnitPosition'):
                    contents['unit_position'] = parts[1]
                elif line.startswith('NumberPositions'):
                    contents['number_positions'] = int(parts[1])
                elif line.startswith('Positions'):
                    break
                else:
                    raise Exception('unknown header line: %r' % (line,))
            # parse positions
            for line, _ in zip(lines, range(contents['number_positions'])):
                contents['positions'].append(
                    [float(coord) for coord in line.strip().split()])
            # parse labels
            # assert next(lines).strip() == 'Labels'
            [contents['labels'].append(line.strip()) for line in lines]
        return contents
