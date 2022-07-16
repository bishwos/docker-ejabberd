import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const getDefaultState = () => {
  return {
    activeChat: null,
    messages: [],
    contacts: [],
    joinedRooms: [],
    knownRooms: [],
    roomsOccupants: [],
    httpFileUploadMaxSize: null,
    isOnline: false,
  }
}

export default new Vuex.Store({
  state: {
    hasNetwork: null,
    ...getDefaultState(),
  },

  getters: {
    publicRooms: (state) => {
      return state.knownRooms.filter((room) => room.isPublic)
    },
    joinedRooms: (state) => {
      return state.knownRooms.filter((room) => state.joinedRooms.includes(room.jid))
    },
    bookmarkedRooms: (state) => {
      return state.knownRooms.filter((room) => room.isBookmarked)
    },
    getRoom: (state) => (jid) => {
      return state.knownRooms.find((room) => room.jid === jid) || {}
    },
    isBookmarked: (state) => (jid) => {
      return state.knownRooms.some((room) => room.jid === jid && room.isBookmarked)
    },
    isJoined: (state) => (jid) => {
      return state.joinedRooms.some((joinedRoomJid) => joinedRoomJid === jid)
    },
    getRoomOccupants: (state) => (jid) => {
      const roomOccupants = state.roomsOccupants.find((roomOccupants) => roomOccupants.roomJid === jid)
      if (roomOccupants) {
        return roomOccupants.occupants
      }
      return []
    },
  },

  mutations: {
    // network status setter
    setNetworkStatus (state, hasNetwork) {
      state.hasNetwork = hasNetwork
    },

    // online client status setter
    setOnline (state, isOnline) {
      state.isOnline = isOnline
    },

    // active chat setter
    setActiveChat (state, payload) {
      state.activeChat = payload.activeChat
      // reset unread messages count for this chat
      function resetUnreadCount (collection) {
        const copy = collection.slice(0)
        const index = copy.findIndex((item) => item.jid === payload.activeChat)
        if (index !== -1) {
          copy[index].unreadCount = 0
        }
        return copy
      }
      switch (payload.type) {
        case 'chat':
          state.contacts = resetUnreadCount(state.contacts)
          break
        case 'groupchat':
          state.knownRooms = resetUnreadCount(state.knownRooms)
          break
      }
    },

    // roster setter
    setRoster (state, contacts) {
      state.contacts = contacts
    },

    // MUC rooms setter
    setKnownRoom (state, room) {
      const rooms = state.knownRooms.slice(0)
      const index = rooms.findIndex((knownRoom) => knownRoom.jid === room.jid)
      if (index === -1) {
        // add room
        state.knownRooms.push(room)
        return
      }
      // update room
      for (const key in room) {
        if (room[key] === null && rooms[index][key] !== null) {
          continue
        }
        rooms[index][key] = room[key]
      }
      state.knownRooms = rooms
    },

    // MUC joined rooms setter
    setJoinedRoom (state, roomJid) {
      const joinedRooms = state.joinedRooms.slice(0)
      const index = joinedRooms.findIndex((knownRoomJid) => knownRoomJid === roomJid)
      if (index === -1) {
        return state.joinedRooms.push(roomJid)
      }
    },

    // contact presence setter
    setContactPresence (state, contactPresence) {
      const contacts = state.contacts.slice(0)
      const index = contacts.findIndex((contact) => contact.jid === contactPresence.jid)
      if (index !== -1) {
        contacts[index].presence = contactPresence.presence
        state.contacts = contacts
      }
    },

    // messages setters
    storePreviousMessages (state, newMessages) {
      let messages = state.messages.slice(0)
      messages = messages.concat(newMessages)
      const vm = this.$app
      messages.sort(function (a, b) {
        return vm.$moment(a.delay).isAfter(vm.$moment(b.delay))
      })
      state.messages = messages
    },
    storeMessage (state, payload) {
      if (payload.message.id) {
        const messages = state.messages.slice(0)
        const index = messages.findIndex((knownMessage) => knownMessage.id === payload.message.id)
        if (index !== -1) {
          // update existing message
          messages[index] = payload.message
          state.messages = messages
          return
        }
      }
      if (payload.message.stanzaId) {
        const messages = state.messages.slice(0)
        const index = messages.findIndex((knownMessage) => knownMessage.stanzaId === payload.message.stanzaId)
        if (index !== -1) {
          // update existing message
          messages[index] = payload.message
          state.messages = messages
          return
        }
      }
      // add new message
      state.messages.push({
        id: payload.message.id,
        stanzaId: payload.message.stanzaId,
        from: payload.message.from,
        to: payload.message.to,
        body: payload.message.body,
        delay: payload.message.delay || null,
        links: payload.message.links || null,
      })

      // order messages by date
      const messages = state.messages.slice(0)
      const vm = this.$app
      messages.sort((a, b) => {
        return vm.$moment(a.delay).isAfter(vm.$moment(b.delay))
      })
      state.messages = messages

      // handle unread messages count
      function addUnreadCount (collection) {
        const copy = collection.slice(0)
        const index = copy.findIndex((item) => item.jid === payload.message.from.bare)
        if (index !== -1) {
          if (copy[index].unreadCount === undefined || copy[index].unreadCount === null) {
            copy[index].unreadCount = 1
          } else {
            copy[index].unreadCount++
          }
        }
        return copy
      }
      if (payload.message.from.bare === state.activeChat) {
        // message is in the displayed chat, do not increment counter
        return
      }
      switch (payload.type) {
        case 'chat':
          state.contacts = addUnreadCount(state.contacts)
          break
        case 'groupchat':
          state.knownRooms = addUnreadCount(state.knownRooms)
          break
      }
    },

    // HTTP file upload max size setter (XEP-0363)
    setHttpFileUploadMaxSize (state, httpFileUploadMaxSize) {
      state.httpFileUploadMaxSize = httpFileUploadMaxSize
    },

    setRoomOccupant (state, { roomJid, jid, presence }) {
      if (!state.roomsOccupants.find((roomOccupants) => roomOccupants.roomJid === roomJid)) {
        // create room occupants list
        state.roomsOccupants.push({
          roomJid,
          occupants: [],
        })
      }
      const roomIndex = state.roomsOccupants.findIndex((roomOccupants) => roomOccupants.roomJid === roomJid)
      const occupant = {
        jid,
        presence,
      }
      const occupantIndex = state.roomsOccupants[roomIndex].occupants.findIndex((occupant) => occupant.jid === jid)
      if (occupantIndex !== -1) {
        // remove previous room occupant
        state.roomsOccupants[roomIndex].occupants.splice(occupantIndex, 1)
      }
      // add room occupant
      state.roomsOccupants[roomIndex].occupants.push(occupant)
    },

    removeRoomOccupant (state, { roomJid, jid }) {
      const roomIndex = state.roomsOccupants.findIndex((roomOccupants) => roomOccupants.roomJid === roomJid)
      if (roomIndex === -1) {
        return
      }
      const index = state.roomsOccupants[roomIndex].occupants.findIndex((occupant) => occupant.jid === jid)
      if (index !== -1) {
        state.roomsOccupants[roomIndex].occupants.splice(index, 1)
      }
    },

    // clear state
    clear (state) {
      const defaultState = getDefaultState()
      Object.keys(defaultState).forEach((key) => {
        state[key] = defaultState[key]
      })
    },

  },
  strict: process.env.NODE_ENV !== 'production',
})
