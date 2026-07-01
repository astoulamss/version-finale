

import React, { useRef, useState, useEffect } from "react";
import { View, Text, TextInput, Pressable, ScrollView } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { Chip } from "../components/ui/Badge";
import { IconButton } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ChatBubble, SkeletonBlock } from "../components/Shared";
import { Ui, ChatMessage, EmployeeProfile } from "../types";
import { isRhRole, isManagerRole, isAdminRole } from "../lib/auth";
import { chatbotService } from "../services/chatbot.service";
const emptyStateExamples = { chat: "Posez-moi vos questions RH" };

export function AssistantScreen({
  aiTyping,
  chatInput,
  messages,
  activeConversationId,
  onInputChange,
  onSend,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
  triggerFeedback,
  ui,
  sessionProfile,
}: {
  aiTyping: boolean;
  chatInput: string;
  messages: ChatMessage[];
  activeConversationId?: number | null;
  onInputChange: (value: string) => void;
  onSend: (prompt?: string) => void;
  onNewConversation?: () => void;
  onSelectConversation?: (id: number) => void;
  onDeleteConversation?: (id: number) => void;
  triggerFeedback: (label?: string) => void;
  ui: Ui;
  sessionProfile?: EmployeeProfile;
}) {
  const { styles, theme } = ui;
  const scrollViewRef = useRef<ScrollView>(null);

  const [conversations, setConversations] = useState<any[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  const fetchConversations = async () => {
    try {
      const res = await chatbotService.getConversations();
      setConversations(res || []);
    } catch (err) {
      console.warn("Failed to load conversations", err);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [activeConversationId]);

  return (
    <View style={{ flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, overflow: 'hidden', borderWidth: 1, borderColor: theme.line }}>
      
      {/* HEADER */}
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line, backgroundColor: '#FFFFFF' }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <Pressable onPress={() => setIsSidebarOpen(!isSidebarOpen)} style={{ padding: 4 }}>
            <Feather name={isSidebarOpen ? "sidebar" : "menu"} size={22} color={theme.text} />
          </Pressable>
          <Feather name="message-square" size={24} color={theme.sky} />
          <View>
            <Text style={{ fontSize: 18, fontWeight: '700', color: theme.text }}>Assistant IA smart RH</Text>
            <Text style={{ fontSize: 13, color: theme.muted }}>En ligne</Text>
          </View>
        </View>
        <Pressable onPress={() => triggerFeedback("Fermer l'assistant")}>
          <Feather name="x" size={24} color={theme.muted} />
        </Pressable>
      </View>

      {/* BODY SPLIT */}
      <View style={{ flex: 1, flexDirection: 'row' }}>
        
        {/* SIDEBAR */}
        {isSidebarOpen && (
          <View style={{ width: 130, borderRightWidth: 1, borderRightColor: theme.line, backgroundColor: '#F9FAFB' }}>
            <View style={{ padding: 8 }}>
              <Pressable 
                onPress={() => onNewConversation?.()}
                style={{ paddingVertical: 8, paddingHorizontal: 4, borderRadius: 6, borderWidth: 1, borderStyle: 'dashed', borderColor: theme.line, alignItems: 'center', flexDirection: 'row', justifyContent: 'center', gap: 4, backgroundColor: '#FFFFFF' }}>
                <Feather name="plus" size={14} color={theme.text} />
                <Text style={{ color: theme.text, fontWeight: '500', fontSize: 12 }}>Nouveau</Text>
              </Pressable>
            </View>

            <ScrollView style={{ flex: 1 }}>
              {conversations.map((conv) => {
                const isActive = activeConversationId === conv.id;
                return (
                  <Pressable 
                    key={conv.id}
                    onPress={() => onSelectConversation?.(conv.id)}
                    style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 8, paddingVertical: 10, backgroundColor: isActive ? '#F3E8FF' : 'transparent', borderLeftWidth: 3, borderLeftColor: isActive ? '#9333EA' : 'transparent' }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 }}>
                      <Text style={{ fontSize: 12 }}>🤖</Text>
                      <Text numberOfLines={1} style={{ color: isActive ? '#6B21A8' : theme.text, fontWeight: isActive ? '600' : '400', fontSize: 12, flex: 1 }}>{conv.title || "Nouvelle"}</Text>
                    </View>
                    <Pressable onPress={async () => {
                      if (onDeleteConversation) {
                        await onDeleteConversation(conv.id);
                        fetchConversations();
                      }
                    }} style={{ paddingLeft: 4 }}>
                      <Feather name="x" size={14} color="#F43F5E" />
                    </Pressable>
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        )}

        {/* MAIN CHAT AREA */}
        <View style={{ flex: 1, backgroundColor: '#F3F4F6', flexDirection: 'column' }}>
          
          <ScrollView
            ref={scrollViewRef}
            onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
            style={{ flex: 1 }}
            contentContainerStyle={{ padding: 16, gap: 16 }}
            showsVerticalScrollIndicator={false}
          >


            <ChatBubble
              message={{
                id: "welcome",
                role: "ai",
                text: `Bonjour ${sessionProfile?.firstName || (sessionProfile as any)?.prenom || "Utilisateur"}. Comment puis-je vous aider aujourd'hui ?`,
                time: "Maintenant",
              }}
              onAction={(action) => {
                if (action === "Mes congés" || action === "Générer attestation") {
                  onSend(action);
                } else {
                  triggerFeedback(`Action lancée : ${action}`);
                }
              }}
              ui={ui}
            />

            {(messages ?? []).map((message) => (
              <ChatBubble key={message.id} message={message} onAction={(action) => triggerFeedback(`Action complétée : ${action}`)} ui={ui} />
            ))}

            {aiTyping && (
              <View style={{ flexDirection: 'row', justifyContent: 'flex-start', marginVertical: 8 }}>
                <View style={{ backgroundColor: '#E5E7EB', padding: 16, borderRadius: 12, borderTopLeftRadius: 4, maxWidth: '80%' }}>
                  <View style={[styles.rowStart, { gap: 4 }]}>
                    <View style={styles.typingDot} />
                    <View style={styles.typingDot} />
                    <View style={styles.typingDot} />
                  </View>
                </View>
              </View>
            )}
          </ScrollView>

          {/* BOTTOM INPUT AREA */}
          <View style={{ padding: 12, borderTopWidth: 1, borderTopColor: theme.line, backgroundColor: '#FFFFFF' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <TextInput
                multiline
                onChangeText={onInputChange}
                placeholder="Posez votre question RH..."
                placeholderTextColor={theme.muted}
                style={{ flex: 1, backgroundColor: '#F9FAFB', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 8, fontSize: 14, borderWidth: 1, borderColor: theme.line, minHeight: 40, maxHeight: 100 }}
                value={chatInput}
              />
              
              <Pressable onPress={() => onSend()} style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: '#1E40AF', alignItems: 'center', justifyContent: 'center' }}>
                <Feather name="send" size={16} color="#ffffff" style={{ marginLeft: -2, marginTop: 2 }} />
              </Pressable>

              <Pressable onPress={() => triggerFeedback("Fermer")} style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#FCA5A5' }}>
                <Feather name="x" size={18} color="#EF4444" />
              </Pressable>
            </View>
          </View>
          
        </View>

      </View>
    </View>
  );
}
