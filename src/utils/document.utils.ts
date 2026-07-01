import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { Platform } from 'react-native';
import { getToken } from './token.utils';
import { API_BASE_URL } from '../services/api';

export const downloadAndOpenDocument = async (
  documentId: string | number,
  title: string = 'document',
  triggerFeedback?: (msg: string) => void
) => {
  try {
    if (triggerFeedback) triggerFeedback("Préparation du téléchargement...");

    const token = await getToken();
    if (!token) {
      if (triggerFeedback) triggerFeedback("Erreur d'authentification");
      return;
    }

    // Prepare filename and URL
    const safeTitle = title.replace(/[^\w\s-]/gi, '').replace(/\s+/g, '_') || `doc_${documentId}`;
    const fileUri = `${FileSystem.documentDirectory}${safeTitle}.pdf`;
    const url = `${API_BASE_URL}/api/documents/${documentId}/download`;

    if (triggerFeedback) triggerFeedback("Téléchargement en cours...");

    const downloadResult = await FileSystem.downloadAsync(url, fileUri, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (downloadResult.status !== 200) {
      throw new Error(`Erreur HTTP: ${downloadResult.status}`);
    }

    if (triggerFeedback) triggerFeedback("Ouverture du document...");

    // Share or open the file
    if (Platform.OS === 'android') {
      const UTI = 'com.adobe.pdf';
      const shareResult = await Sharing.shareAsync(downloadResult.uri, {
        mimeType: 'application/pdf',
        dialogTitle: 'Ouvrir le document',
        UTI: UTI
      });
    } else {
      await Sharing.shareAsync(downloadResult.uri);
    }
  } catch (error) {
    console.error("Erreur de téléchargement", error);
    if (triggerFeedback) triggerFeedback("Échec du téléchargement ou d'ouverture du document.");
  }
};
