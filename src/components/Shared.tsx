

import React from "react";
import { View, Text, Switch, Pressable } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Ui, EmployeeProfile, FeatherName, OnboardingTask, AiReply, DocumentCategory, RecentDocument, HrNotification, StatusTone, ChatMessage } from "../types";
import { Card } from "./ui/Card";
import { Chip, StatusBadge } from "./ui/Badge";
import { toneColor, statusToneFromDocument, getDocumentStatusLabel } from "../theme/utils";

export function SkeletonBlock({ ui }: { ui: Ui }) {
  const { styles } = ui;
  return (
    <View style={styles.skeletonBlock}>
      <View style={styles.skeletonLineLarge} />
      <View style={styles.skeletonLine} />
      <View style={styles.skeletonLineShort} />
    </View>
  );
}

function renderMarkdown(text: string, baseStyle: any) {
  if (!text) return null;
  // Simple markdown parser for **bold**
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return (
    <Text style={baseStyle}>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <Text key={i} style={[baseStyle, { fontWeight: 'bold' }]}>{part.slice(2, -2)}</Text>;
        }
        return part;
      })}
    </Text>
  );
}


export function PrivacyBadge({ label, ui }: { label: string; ui: Ui }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: ui.theme.surfaceAlt, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, gap: 4 }}>
      <Feather name="lock" size={11} color={ui.theme.muted} />
      <Text style={{ fontSize: 10, color: ui.theme.muted, fontWeight: '800', textTransform: 'uppercase' }}>{label}</Text>
    </View>
  );
}

export function Timeline({ steps, ui }: { steps: Array<{ id: string; label: string; detail: string; status: string }>; ui: Ui }) {
  const { styles, theme } = ui;

  return (
    <Card ui={ui}>
      {steps.map((step, index) => (
        <View key={step.id} style={styles.timelineRow}>
          <View style={styles.timelineTrack}>
            <View style={[styles.timelineDot, { backgroundColor: step.status === "done" ? theme.emerald : step.status === "active" ? theme.sky : theme.line }]} />
            {index < steps.length - 1 && <View style={styles.timelineLine} />}
          </View>
          <View style={styles.flex1}>
            <Text style={styles.bodyStrong}>{step.label}</Text>
            <Text style={styles.mutedText}>{step.detail}</Text>
          </View>
        </View>
      ))}
    </Card>
  );
}

export function Stepper({ current, labels, ui }: { current: number; labels: string[]; ui: Ui }) {
  const { styles, theme } = ui;
  return (
    <View style={styles.stepper}>
      {labels.map((label, index) => {
        const step = index + 1;
        const active = step <= current;
        return (
          <View key={label} style={styles.stepItem}>
            <View style={[styles.stepCircle, active && { backgroundColor: theme.sky }]}>
              <Text style={[styles.stepCircleText, active && { color: "#ffffff" }]}>{step}</Text>
            </View>
            <Text style={styles.stepLabel}>{label}</Text>
          </View>
        );
      })}
    </View>
  );
}

export function ProgressBar({ value, ui }: { value: number; ui: Ui }) {
  const { styles } = ui;
  return (
    <View style={styles.progressTrack}>
      <View style={[styles.progressFill, { width: `${Math.min(Math.max(value, 0), 100)}%` }]} />
    </View>
  );
}

export function ProfileSummary({ sessionProfile, ui }: { sessionProfile: EmployeeProfile; ui: Ui }) {
  return (
    <View style={ui.styles.infoGrid}>
      <InfoRow label="Matricule" value={sessionProfile.employeeId} ui={ui} />
      <InfoRow label="Manager" value={sessionProfile.manager} ui={ui} />
      <InfoRow label="Date d'entree" value={sessionProfile.startDate} ui={ui} />
      <InfoRow label="Bureau" value={sessionProfile.office} ui={ui} />
    </View>
  );
}

export function InfoRow({ label, value, ui }: { label: string; value: string; ui: Ui }) {
  const { styles } = ui;
  return (
    <View style={styles.infoRow}>
      <Text style={styles.metaText}>{label}</Text>
      <Text style={styles.bodyStrong}>{value}</Text>
    </View>
  );
}

export function InputCard({ icon, label, secure, value, ui }: { icon: FeatherName; label: string; secure?: boolean; value: string; ui: Ui }) {
  const { styles, theme } = ui;
  return (
    <View style={styles.inputCard}>
      <Feather name={icon} size={18} color={theme.sky} />
      <View style={styles.flex1}>
        <Text style={styles.metaText}>{label}</Text>
        <Text style={styles.inputText}>{secure ? "********" : value}</Text>
      </View>
    </View>
  );
}

export function SettingRow({ children, icon, label, ui }: { children: React.ReactNode; icon: FeatherName; label: string; ui: Ui }) {
  const { styles, theme } = ui;
  return (
    <View style={styles.settingRow}>
      <View style={styles.rowStart}>
        <Feather name={icon} size={18} color={theme.sky} />
        <Text style={styles.bodyStrong}>{label}</Text>
      </View>
      {children}
    </View>
  );
}

export function SettingSwitch({
  icon,
  label,
  onValueChange,
  ui,
  value,
}: {
  icon: FeatherName;
  label: string;
  onValueChange: (value: boolean) => void;
  ui: Ui;
  value: boolean;
}) {
  const { theme } = ui;
  return (
    <SettingRow icon={icon} label={label} ui={ui}>
      <Switch
        onValueChange={onValueChange}
        thumbColor={value ? theme.emerald : theme.muted}
        trackColor={{ false: theme.line, true: theme.emeraldSoft }}
        value={value}
      />
    </SettingRow>
  );
}

export function DetailList({ icon, items, title, onPressItem, ui }: { icon: FeatherName; items: string[]; title: string; onPressItem?: () => void; ui: Ui }) {
  const { styles, theme } = ui;
  return (
    <Card ui={ui}>
      <View style={styles.rowStart}>
        <Feather name={icon} size={17} color={theme.sky} />
        <Text style={styles.cardTitle}>{title}</Text>
      </View>
      {items.map((item) => (
        <Pressable key={item} onPress={onPressItem} style={({ pressed }) => [pressed && { opacity: 0.5 }]}>
          <Text style={styles.bodyText}>- {item}</Text>
        </Pressable>
      ))}
    </Card>
  );
}

export function ChatBubble({ message, ui, onAction }: { message: ChatMessage; ui: Ui; onAction?: (action: string) => void }) {
  const { styles, theme } = ui;
  const isEmployee = message.role === "employee";

  return (
    <View style={[styles.chatBubble, isEmployee ? styles.chatBubbleEmployee : styles.chatBubbleAi]}>
      {isEmployee && <Text style={styles.employeeMessageText}>{message.text}</Text>}
      {!isEmployee && !message.reply && renderMarkdown(message.text, [styles.bodyText, { color: '#1F2937' }])}
      {!isEmployee && message.reply && (
        <View style={styles.stackSmall}>
          <View style={styles.rowBetween}>
            <StatusBadge label={replyKindLabel(message.reply.kind)} tone={replyTone(message.reply)} ui={ui} />
            <Text style={styles.metaText}>{message.reply.source ?? "Local"}</Text>
          </View>
          <Text style={styles.cardTitle}>{message.reply.title}</Text>
          <Text style={styles.bodyText}>{message.reply.text}</Text>
          {message.reply.options && (
            <View style={styles.chipWrap}>
              {message.reply.options.map((option: string) => (
                <Chip key={option} label={option} onPress={() => onAction?.(option)} ui={ui} />
              ))}
            </View>
          )}
          <View style={styles.actionButtonRow}>
            {message.reply.actions.map((action: string) => (
              <Pressable key={action} style={styles.inlineAction} onPress={() => onAction?.(action)}>
                <Text style={styles.inlineActionText}>{action}</Text>
              </Pressable>
            ))}
          </View>
          {message.reply.kind === "permission-denied" && (
            <View style={styles.securityNote}>
              <Feather name="shield" size={15} color={theme.rose} />
              <Text style={styles.microcopy}>Protection donnees RH activee</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}
export function replyKindLabel(kind: AiReply["kind"]) {
  const labels = {
    answer: "Reponse autorisee",
    clarification: "Clarification",
    "permission-denied": "Acces refuse",
    escalation: "Escalade RH",
    error: "Erreur reseau",
  };
  return labels[kind];
}

export function replyTone(reply: AiReply): StatusTone {
  if (reply.kind === "permission-denied" || reply.kind === "error") {
    return "critical";
  }
  if (reply.kind === "escalation" || reply.kind === "clarification") {
    return "warning";
  }
  return "success";
}

export function DocumentCategoryCard({
  category,
  onStartDocument,
  ui,
}: {
  category: DocumentCategory;
  onStartDocument: (template: string) => void;
  ui: Ui;
}) {
  const { styles, theme } = ui;

  return (
    <Card ui={ui}>
      <View style={styles.rowStart}>
        <View style={styles.actionIcon}>
          <Feather name={category.icon as FeatherName} size={19} color={theme.sky} />
        </View>
        <View style={styles.flex1}>
          <Text style={styles.cardTitle}>{category.title}</Text>
          <Text style={styles.bodyText}>{category.description}</Text>
        </View>
      </View>
      <View style={styles.chipWrap}>
        {category.templates.map((template) => (
          <Chip key={template} label={template} onPress={() => onStartDocument(template)} ui={ui} active />
        ))}
      </View>
    </Card>
  );
}

export function DocumentRow({ document, onPress, ui }: { document: RecentDocument; onPress: () => void; ui: Ui }) {
  const { styles, theme } = ui;

  return (
    <Pressable onPress={onPress} style={styles.documentRow}>
      <View style={styles.documentIcon}>
        <Feather name="file-text" size={18} color={theme.sky} />
      </View>
      <View style={styles.flex1}>
        <Text style={styles.bodyStrong}>{document.title}</Text>
        <Text style={styles.mutedText}>
          {document.date} - {document.owner}
        </Text>
      </View>
      <StatusBadge label={getDocumentStatusLabel(document.status)} tone={statusToneFromDocument(document.status)} ui={ui} />
    </Pressable>
  );
}

export function NotificationCard({
  compact,
  notification,
  onMarkRead,
  onPress,
  ui,
}: {
  compact?: boolean;
  notification: HrNotification;
  onMarkRead: () => void;
  onPress?: () => void;
  ui: Ui;
}) {
  const { styles, theme } = ui;

  return (
    <Card tone={notification.priority} onPress={onPress} ui={ui}>
      <View style={styles.rowStart}>
        <View style={[styles.notificationStripe, { backgroundColor: toneColor(notification.priority, theme) }]} />
        <View style={styles.flex1}>
          <View style={styles.rowBetween}>
            <Text style={styles.cardTitle}>{notification.title}</Text>
            {notification.unread && <View style={styles.smallUnreadDot} />}
          </View>
          <Text style={styles.bodyText}>{notification.body}</Text>
          <View style={styles.metaRow}>
            <StatusBadge label={notification.category} tone={notification.priority} ui={ui} />
            <Text style={styles.metaText}>{notification.time}</Text>
          </View>
        </View>
      </View>
      {!compact && (
        <Pressable onPress={onMarkRead} style={styles.swipeAction}>
          <Feather name="check" size={15} color={theme.emerald} />
          <Text style={styles.linkText}>Marquer comme lu</Text>
        </Pressable>
      )}
    </Card>
  );
}
export function StatusIcon({ status, ui }: { status: OnboardingTask["status"]; ui: Ui }) {
  const { styles, theme } = ui;
  const icon = status === "done" ? "check-circle" : status === "late" ? "alert-circle" : status === "active" ? "play-circle" : "circle";
  const color = status === "done" ? theme.emerald : status === "late" ? theme.rose : status === "active" ? theme.sky : theme.muted;
  return (
    <View style={styles.statusIcon}>
      <Feather name={icon} size={18} color={color} />
    </View>
  );
}
