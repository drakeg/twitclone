# Ripple rebrand testing

Automated regression coverage verifies that the rendered home and
authentication pages contain Ripple branding and do not render the former
TwitClone product name. A focused source check also guards the runtime paths
against reintroducing `datetime.utcnow()`.
