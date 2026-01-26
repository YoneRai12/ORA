
import { signIn } from "@/auth"

export default function Page() {
    return (
        <div className="flex h-screen w-full flex-col items-center justify-center bg-black text-white">
            <div className="w-full max-w-md space-y-8 rounded-2xl bg-zinc-900 p-10 shadow-2xl border border-zinc-800">
                <div className="text-center">
                    <h1 className="text-5xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
                        ORA
                    </h1>
                    <h2 className="text-2xl font-semibold text-zinc-100">
                        Welcome Back
                    </h2>
                    <p className="mt-2 text-sm text-zinc-400">
                        Sign in to access your dashboard
                    </p>
                </div>

                <form
                    action={async () => {
                        "use server"
                        await signIn("discord", { redirectTo: "/dashboard" })
                    }}
                    className="mt-8 space-y-6"
                >
                    <button
                        type="submit"
                        className="group relative flex w-full justify-center rounded-lg bg-[#5865F2] px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-[#4752C4] hover:shadow-lg hover:shadow-indigo-500/20 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-zinc-900"
                    >
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                            <svg
                                className="h-5 w-5 text-indigo-300 group-hover:text-indigo-200"
                                fill="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1892.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.1023.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189z" />
                            </svg>
                        </span>
                        Sign in with Discord
                    </button>
                </form>
            </div>
        </div>
    )
}
