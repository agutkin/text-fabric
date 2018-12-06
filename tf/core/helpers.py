import os
import sys
import re

LETTER = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
VALID = set('_0123456789') | LETTER

WARN32 = '''WARNING: you are not running a 64-bit implementation of Python.
You may run into memory problems if you load a big data set.
Consider installing a 64-bit Python.
'''

MSG64 = '''Running on 64-bit Python'''


def splitModRef(moduleRef):
  parts = moduleRef.split('/', 2)

  if len(parts) < 2:
    console(
        f'''
Module ref "{moduleRef}" is not "{{org}}/{{repo}}/{{path}}"
''',
        error=True,
    )
    return None

  if len(parts) == 2:
    parts.append('')

  return parts


def camel(name):
  if not name:
    return name
  temp = name.replace('_', ' ').title().replace(' ', '')
  return temp[0].lower() + temp[1:]


def check32():
  warn = ''
  msg = ''
  on32 = sys.maxsize < 2**63 - 1
  if on32 < 2**63 - 1:
    warn = WARN32
  else:
    msg = MSG64
  return (on32, warn, msg)


def console(msg, error=False):
  msg = msg[1:] if msg.startswith('\n') else msg
  msg = msg[0:-1] if msg.endswith('\n') else msg
  target = sys.stderr if error else sys.stdout
  target.write(f'{msg}\n')
  target.flush()


def cleanName(name):
  clean = ''.join(c if c in VALID else '_' for c in name)
  if clean == '' or not clean[0] in LETTER:
    clean = 'x' + clean
  return clean


def isClean(name):
  if name is None or len(name) == 0 or name[0] not in LETTER:
    return False
  return all(c in VALID for c in name[1:])


def setDir(obj):
  obj.homeDir = os.path.expanduser('~').replace('\\', '/')
  obj.curDir = os.getcwd().replace('\\', '/')
  (obj.parentDir, x) = os.path.split(obj.curDir)


def expandDir(obj, dirName):
  if dirName.startswith('~'):
    dirName = dirName.replace('~', obj.homeDir, 1)
  elif dirName.startswith('..'):
    dirName = dirName.replace('..', obj.parentDir, 1)
  elif dirName.startswith('.'):
    dirName = dirName.replace('.', obj.curDir, 1)
  return dirName


def setFromSpec(spec):
  covered = set()
  for r_str in spec.split(','):
    bounds = r_str.split('-')
    if len(bounds) == 1:
      covered.add(int(r_str))
    else:
      b = int(bounds[0])
      e = int(bounds[1])
      if e < b:
        (b, e) = (e, b)
      for n in range(b, e + 1):
        covered.add(n)
  return covered


def rangesFromSet(nodeSet):
  ranges = []
  curstart = None
  curend = None
  for n in sorted(nodeSet):
    if curstart is None:
      curstart = n
      curend = n
    elif n == curend + 1:
      curend = n
    else:
      ranges.append((curstart, curend))
      curstart = n
      curend = n
  if curstart is not None:
    ranges.append((curstart, curend))
  return ranges


def rangesFromList(nodeList):  # the list must be sorted
  ranges = []
  curstart = None
  curend = None
  for n in nodeList:
    if curstart is None:
      curstart = n
      curend = n
    elif n == curend + 1:
      curend = n
    else:
      ranges.append((curstart, curend))
      curstart = n
      curend = n
  if curstart is not None:
    ranges.append((curstart, curend))
  return ranges


def specFromRanges(ranges):  # ranges must be normalized
  return ','.join('{}'.format(r[0]) if r[0] == r[1] else '{}-{}'.format(*r) for r in ranges)


def valueFromTf(tf):
  return '\\'.join(x.replace('\\t', '\t').replace('\\n', '\n') for x in tf.split('\\\\'))


def tfFromValue(val):
  return (
      str(val)
      if type(val) is int else val.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
  )


def makeInverse(data):
  inverse = {}
  for n in data:
    for m in data[n]:
      inverse.setdefault(m, set()).add(n)
  return inverse


def makeInverseVal(data):
  inverse = {}
  for n in data:
    for (m, val) in data[n].items():
      inverse.setdefault(m, {})[n] = val
  return inverse


def nbytes(by):
  units = ['B', 'KB', 'MB', 'GB', 'TB']
  for i in range(len(units)):
    if by < 1024 or i == len(units) - 1:
      fmt = '{:>5}{}' if i == 0 else '{:>5.1f}{}'
      return fmt.format(by, units[i])
    by /= 1024


def collectFormats(config):
  varPattern = re.compile(r'\{([^}]+)\}')
  featureSet = set()

  def collectFormat(tpl):
    features = []

    def varReplace(match):
      varText = match.group(1)
      fts = tuple(varText.split('/'))
      features.append(fts)
      for ft in fts:
        featureSet.add(ft)
      return '{}'

    rtpl = varPattern.sub(varReplace, tpl)
    return (rtpl, tuple(features))

  formats = {}
  for (fmt, tpl) in sorted(config.items()):
    if fmt.startswith('fmt:'):
      formats[fmt[4:]] = collectFormat(tpl)
  return (formats, sorted(featureSet))


def compileFormats(cformats, features):
  xformats = {}
  for (fmt, (rtpl, feats)) in sorted(cformats.items()):
    tpl = rtpl.replace('\\n', '\n').replace('\\t', '\t')
    xformats[fmt] = compileFormat(tpl, feats, features)
  return xformats


def compileFormat(rtpl, feats, features):
  replaceFuncs = []
  for feat in feats:
    replaceFuncs.append(makeFunc(feat, features))

  def g(n):
    values = tuple(replaceFunc(n) for replaceFunc in replaceFuncs)
    return rtpl.format(*values)

  return g


def makeFunc(feat, features):
  if len(feat) == 1:
    ft = feat[0]
    f = features[ft].data
    return (lambda n: f.get(n, ''))
  elif len(feat) == 2:
    (ft1, ft2) = feat
    f1 = features[ft1].data
    f2 = features[ft2].data
    return (lambda n: (f1.get(n, f2.get(n, ''))))


def itemize(string, sep=None):
  if not string:
    return []
  if not sep:
    return string.strip().split()
  return string.strip().split(sep)


def project(iterableOfTuples, maxDimension):
  if maxDimension == 1:
    return {r[0] for r in iterableOfTuples}
  return {r[0:maxDimension] for r in iterableOfTuples}


msgLinePat = '^( *[0-9]+) (.*)$'
msgLineRe = re.compile(msgLinePat)


def shapeMessages(messages):
  if type(messages) is str:
    messages = messages.split('\n')
  html = []
  for msg in messages:
    if type(msg) is tuple:
      (error, nl, msgRep) = msg
      match = msgLineRe.match(msgRep)
      msg = msgRep + ('<br/>' if nl else '')
      className = 'eline' if error and not match else 'tline'
    else:
      match = msgLineRe.match(msg)
      className = 'tline' if match else 'eline'
      msg = msg.replace('\n', '<br/>')
    html.append(f'''
      <span class="{className.lower()}">{msg}</span>
    ''')
  return ''.join(html)