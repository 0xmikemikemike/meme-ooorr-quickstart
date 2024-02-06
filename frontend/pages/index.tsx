import { Layout } from "@/components/Layout/Layout";
import { Marketplace } from "@/components/Marketplace/Marketplace";
import { YourAgents } from "@/components/YourAgents/YourAgents";
import { useTabs } from "@/hooks/useTabs";
import { Button, Tabs, type TabsProps } from "antd";
import { useMemo } from "react";



export default function Home() {
  
  const tabs: TabsProps["items"] = useMemo(()=>[
  {
    key: "1",
    label: "Your Agents",
    children: <YourAgents />,
  },
  {
    key: "2",
    label: "Marketplace",
    children: <Marketplace />,
  },
  {
    key: "3",
    label: "Test",
    children: <Button />,
  }
],[]);
  
  const { activeTab, setActiveTab } = useTabs();




  return (
    <Layout>
      <Tabs
        items={tabs}
        activeKey={activeTab}
        onChange={(activeKey: string) => setActiveTab(activeKey)}
      />
    </Layout>
  );
}
