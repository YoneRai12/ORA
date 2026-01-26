import { auth } from "@/auth"
import { redirect } from "next/navigation"
import DashboardView from "@/app/components/DashboardView"

interface PageProps {
    params: Promise<{ guildId: string }>
}

export default async function GuildDashboard({ params }: PageProps) {
    const session = await auth()

    if (!session?.user) {
        redirect("/login")
    }

    const resolvedParams = await params
    const guildId = resolvedParams.guildId

    // In a real implementation, we would verify membership here:
    // await verifyGuildMembership(session.accessToken, guildId)

    // Mock Guild Name for now, or fetch if possible
    const guildName = guildId === "1307177622366851135" ? "Development Server" : "Community Server"

    return <DashboardView guildId={guildId} guildName={guildName} />
}
