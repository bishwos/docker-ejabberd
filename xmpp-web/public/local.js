// eslint-disable-next-line no-unused-vars, no-var
var config = {
  name: 'XMPP web',
  transports: {
    bosh: 'https://localhost:5443/bosh/',
    websocket: 'wss://localhost:5222'
  },
  hasGuestAccess: true,
  hasRegisteredAccess: true,
  anonymousHost: null,
  // anonymousHost: 'anon.domain-xmpp.ltd',
  isTransportsUserAllowed: false,
  hasHttpAutoDiscovery: false,
  resource: 'Web XMPP',
  defaultDomain: 'localhost',
  defaultMuc: null,
  // defaultMuc: 'conference.domain-xmpp.ltd',
  isStylingDisabled: false,
}
