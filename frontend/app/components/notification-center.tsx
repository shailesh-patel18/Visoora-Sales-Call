"use client";

import React, { useState, useEffect } from "react";
import { Bell, CheckCircle, Clock, Calendar, AlertCircle } from "lucide-react";

type Notification = {
  id: string;
  type: 'success' | 'warning' | 'info' | 'calendar';
  title: string;
  description: string;
  time: string;
};

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasUnread, setHasUnread] = useState(true);

  // Hardcoded for PMF MVP presentation
  const notifications: Notification[] = [
    {
      id: "1",
      type: "success",
      title: "Research completed",
      description: "Mission Alpha processed 421 companies",
      time: "2m ago"
    },
    {
      id: "2",
      type: "warning",
      title: "Approval Required",
      description: "12 emails waiting in your inbox",
      time: "5m ago"
    },
    {
      id: "3",
      type: "calendar",
      title: "Meeting Booked",
      description: "Acme Health (John Smith)",
      time: "Yesterday"
    },
    {
      id: "4",
      type: "info",
      title: "Learning Updated",
      description: "Adjusted pricing objection handling",
      time: "Today"
    }
  ];

  const toggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) setHasUnread(false);
  };

  return (
    <div className="relative">
      <button 
        onClick={toggle}
        className="relative p-2 text-gray-400 hover:text-white transition-colors rounded-full hover:bg-white/5 focus:outline-none"
      >
        <Bell className="w-5 h-5" />
        {hasUnread && (
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-[#111]"></span>
        )}
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-[#18181B] border border-[hsl(var(--border-subtle))] rounded-xl shadow-2xl z-50 overflow-hidden transform origin-top-right transition-all">
            <div className="px-4 py-3 border-b border-[hsl(var(--border-subtle))] bg-[#1F1F23] flex justify-between items-center">
              <h3 className="font-semibold text-white">Notifications</h3>
              <button className="text-xs text-[hsl(var(--brand-primary))] hover:text-white transition-colors">Mark all as read</button>
            </div>
            <div className="max-h-[400px] overflow-y-auto">
              {notifications.map((n) => (
                <div key={n.id} className="p-4 border-b border-[hsl(var(--border-subtle))]/50 hover:bg-white/5 transition-colors cursor-pointer flex gap-3">
                  <div className="mt-0.5">
                    {n.type === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                    {n.type === 'warning' && <AlertCircle className="w-4 h-4 text-amber-400" />}
                    {n.type === 'calendar' && <Calendar className="w-4 h-4 text-[hsl(var(--brand-primary))]" />}
                    {n.type === 'info' && <Clock className="w-4 h-4 text-blue-400" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{n.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{n.description}</p>
                    <p className="text-[10px] text-gray-500 mt-1">{n.time}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-2 bg-[#141415] text-center border-t border-[hsl(var(--border-subtle))]">
              <button className="text-xs text-gray-400 hover:text-white transition-colors w-full py-1">View all activity</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
