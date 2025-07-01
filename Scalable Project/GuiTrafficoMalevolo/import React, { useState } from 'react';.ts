import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

export default function SimulationGUI() {
  const [duration, setDuration] = useState("15");
  const [log, setLog] = useState<string[]>([]);
  const [simulationRunning, setSimulationRunning] = useState(false);

  // Fix: Add state for attack/anomaly selection and calendar
  const [attackType, setAttackType] = useState("Port scan");
  const [attackDate, setAttackDate] = useState<Date | undefined>(new Date());
  const [anomalyType, setAnomalyType] = useState("DNS request spike");
  const [anomalyEnabled, setAnomalyEnabled] = useState(false);

  const handleStart = () => {
    setSimulationRunning(true);
    setLog((prev) => [...prev, "Simulation started"]);
  };

  const handleStop = () => {
    setSimulationRunning(false);
    setLog((prev) => [...prev, "Simulation stopped"]);
  };

  // Fix: Implement schedule handlers
  const handleScheduleAttack = () => {
    setLog((prev) => [
      ...prev,
      `Attack scheduled: ${attackType} at ${attackDate?.toLocaleString() ?? "unknown time"}`
    ]);
  };

  const handleScheduleAnomaly = () => {
    if (anomalyEnabled) {
      setLog((prev) => [
        ...prev,
        `Anomaly scheduled: ${anomalyType}`
      ]);
    } else {
      setLog((prev) => [
        ...prev,
        "Enable anomaly scheduling to schedule an anomaly"
      ]);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Network Traffic Simulation Control Panel</h1>

      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center space-x-4">
            <Input
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder="Duration in minutes"
              min={1}
            />
            <Button onClick={handleStart} disabled={simulationRunning}>Start</Button>
            <Button onClick={handleStop} disabled={!simulationRunning} variant="destructive">Stop</Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="attacks">
        <TabsList>
          <TabsTrigger value="attacks">Schedule Attacks</TabsTrigger>
          <TabsTrigger value="anomalies">Schedule Anomalies</TabsTrigger>
          <TabsTrigger value="logs">Live Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="attacks">
          <Card className="mt-4">
            <CardContent className="p-4 space-y-4">
              <p className="font-medium">Choose attack type and time:</p>
              <select
                className="border rounded p-2 w-full"
                value={attackType}
                onChange={(e) => setAttackType(e.target.value)}
              >
                <option>Port scan</option>
                <option>SSH brute force</option>
                <option>Lateral movement</option>
              </select>
              <Calendar
                mode="single"
                selected={attackDate}
                onSelect={setAttackDate}
                className="w-fit"
              />
              <Button onClick={handleScheduleAttack}>Schedule Attack</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="anomalies">
          <Card className="mt-4">
            <CardContent className="p-4 space-y-4">
              <p className="font-medium">Choose anomaly type:</p>
              <select
                className="border rounded p-2 w-full"
                value={anomalyType}
                onChange={(e) => setAnomalyType(e.target.value)}
              >
                <option>DNS request spike</option>
                <option>Unexpected port usage</option>
                <option>Internal DB access anomaly</option>
              </select>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={anomalyEnabled}
                  onCheckedChange={setAnomalyEnabled}
                  // @ts-ignore
                  aria-label="Enable anomaly scheduling"
                />
                <span>Enable anomaly scheduling</span>
              </div>
              <Button onClick={handleScheduleAnomaly}>Schedule Anomaly</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card className="mt-4">
            <CardContent className="p-4">
              <h2 className="font-medium mb-2">Live Log Output</h2>
              <Textarea
                className="w-full h-60"
                readOnly
                value={log.join("\n")}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}