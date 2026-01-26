import { auth } from "@/auth"
import Link from "next/link"
import { redirect } from "next/navigation"

export default async function DashboardPage() {
    const session = await auth()

    // Redirect if not authenticated
    if (!session?.user) {
        redirect("/login")
    }

    // This data would ideally come from the Discord API to check mutual guilds
    // For now we will mock this or fetch basic user guilds if possible
    // Since we need to use the token to fetch guilds, and we might not have stored it in session explicitly without callbacks.
    // Let's assume for MVP we just show a "Select Server" placeholder or try to fetch if we have the token.

    // Actually, to list servers we need the 'guilds' scope and the access token. 
    // In v5 beta, accessing the token in server component can be tricky if not added to session.
    // Let's create a simple Server Selector UI.

    return (
        <div className="min-h-screen bg-black text-white p-8 font-sans">
            <div className="max-w-4xl mx-auto">
                <header className="flex justify-between items-center mb-12">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                            Select Server
                        </h1>
                        <p className="text-gray-400 mt-2">
                            Choose a server to view its specific dashboard.
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            {session.user.image && (
                                <img src={session.user.image} alt="User" className="w-8 h-8 rounded-full" />
                            )}
                            <span className="font-semibold text-sm">{session.user.name}</span>
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Mock Server for Dev */}
                    <Link href="/dashboard/1307177622366851135" className="group">
                        <div className="bg-[#1f1f1f] border border-white/10 p-6 rounded-2xl hover:border-blue-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 font-bold text-xl group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                    DEV
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg text-white group-hover:text-blue-400 transition-colors">Development Server</h3>
                                    <p className="text-xs text-gray-500 font-mono">ID: 1307177622366851135</p>
                                </div>
                            </div>
                        </div>
                    </Link>

                    {/* Placeholder for other servers */}
                    <div className="bg-[#1f1f1f]/50 border border-white/5 p-6 rounded-2xl flex items-center justify-center border-dashed">
                        <p className="text-gray-600 text-sm">More servers will appear here...</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
