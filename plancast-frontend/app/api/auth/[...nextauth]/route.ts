import NextAuth from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { compare } from "bcryptjs"

const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: {  label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // This is a mock authorization. Replace with a real database lookup.
        const mockUser = {
          id: "1",
          email: "demo@plancast.app",
          name: "Demo User",
          password: "$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhH8eG" // "password123"
        }

        if (credentials?.email === mockUser.email && credentials?.password) {
          const isPasswordValid = await compare(credentials.password, mockUser.password)
          if (isPasswordValid) {
            return { id: mockUser.id, name: mockUser.name, email: mockUser.email }
          }
        }
        return null
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
      }
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string
      }
      return session
    }
  },
  pages: {
    signIn: '/auth/signin',
  }
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
