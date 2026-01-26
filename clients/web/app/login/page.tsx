import { signIn } from "@/auth"

export default function LoginPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-4">
            <div className="bg-[#1f1f1f] p-8 rounded-2xl shadow-2xl border border-white/10 max-w-md w-full text-center">
                <h1 className="text-3xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    Login Required
                </h1>
                <p className="text-gray-400 mb-8">
                    This dashboard is restricted to verified Discord server members. Please sign in to continue.
                </p>

                <form
                    action={async () => {
                        "use server"
                        await signIn("discord", { redirectTo: "/dashboard" })
                    }}
                >
                    <button
                        type="submit"
                        className="w-full bg-[#5865F2] hover:bg-[#4752C4] text-white font-bold py-3 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
                    >
                        <svg viewBox="0 0 127.14 96.36" className="w-6 h-6 fill-current">
                            <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.11,77.11,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.89,105.89,0,0,0,126.6,80.22c1.24-23.28-1.52-47.56-18.9-72.15ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z" />
                        </svg>
                        Sign in with Discord
                    </button>
                </form>
            </div>
        </div>
    )
}
