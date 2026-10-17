"""Apply only the seven pre-reviewed proposed files after the REST gate."""
import s10_p0_21_contract as c
c.gate();proposal=c.read(c.OUT/'proposed-product-contract.json')
assert c.git('rev-parse','HEAD')==c.BASE
for target,f in proposal['files'].items():
    data=(c.ROOT/f['proposed_file']).read_bytes();assert c.sha(data)==f['sha256']
    assert target.startswith('ydental_settlement/')
    c.ROOT.joinpath(target).write_bytes(data)
print('seven frozen product files applied; no runtime operations')
