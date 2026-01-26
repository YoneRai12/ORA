
import { auth, signOut } from "@/auth"
import { redirect } from "next/navigation"

export default async function Dashboard() {
    const session = await auth()

    if (!session) {
        redirect("/login")
    }

    return (
        <div className="min-h-screen bg-black text-white">
            {/* Header */}
            <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-50">
                <div className="container mx-auto flex h-16 items-center justify-between px-4">
                    <div className="flex items-center gap-4">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500" />
                        <span className="text-xl font-bold tracking-tight">ORA Dashboard</span>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3">
                            {session.user?.image && (
                                <img
                                    src={session.user.image}
                                    alt="User"
                                    className="h-8 w-8 rounded-full ring-2 ring-zinc-700"
                                />
                            )}
                            <span className="text-sm font-medium text-zinc-300">
                                {session.user?.name}
                            </span>
                        </div>

                        <form
                            action={async () => {
                                "use server"
                                await signOut({ redirectTo: "/" })
                            }}
                        >
                            <button
                                className="rounded-md bg-zinc-800 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors"
                                type="submit"
                            >
                                Sign Out
                            </button>
                        </form>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto p-8">
                <h1 className="text-3xl font-bold mb-8">Overview</h1>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
                        <h3 className="text-lg font-medium text-zinc-400 mb-2">My Access</h3>
                        <p className="text-3xl font-bold">Authorized</p>
                        <div className="mt-4 text-sm text-green-400 flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                            Active Session
                        </div>
                    </div>

                    {/* Placeholder stats */}
                    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 opacity-50">
                        <h3 className="text-lg font-medium text-zinc-400 mb-2">Bot Status</h3>
                        <p className="text-3xl font-bold">Online</p>
                    </div>
                    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 opacity-50">
                        <h3 className="text-lg font-medium text-zinc-400 mb-2">Credits</h3>
                        <p className="text-3xl font-bold">∞</p>
                    </div>
                </div>
            </main>
        </div>
    )
}
