
import NextAuth from "next-auth"
import Discord from "next-auth/providers/discord"

export const { handlers, signIn, signOut, auth } = NextAuth({
    providers: [Discord],
    pages: {
        signIn: "/login",
    },
    callbacks: {
        async session({ session, token }) {
            // Add more data to session here if needed (e.g. user ID)
            if (session.user) {
                // session.user.id = token.sub // if using JWT
            }
            return session
        },
    },
})
