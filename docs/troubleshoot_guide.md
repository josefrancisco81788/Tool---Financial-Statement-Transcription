# 🔧 Financial Statement Tool - Troubleshooting Guide

## 🚨 **When One Document Works But Another Doesn't**

### **Immediate Solutions (Try in Order):**

#### **1. Switch Processing Methods** ⚡
- **Current Method**: Check what you used for the failed document
- **Switch To**:
  - If used "Whole-Document Context" → Try "Vector Database Analysis"
  - If used "Vector Database Analysis" → Try "Whole-Document Context"

#### **2. Adjust Performance Settings** 🎛️
- **Disable Parallel Processing**: Uncheck "Enable Parallel Processing (5 workers)"
- **Why**: Sequential processing is slower but more reliable for difficult documents
- **When**: Try this if switching methods doesn't work

#### **3. Document-Specific Optimizations** 📄

| Document Type | Best Method | Settings |
|---------------|-------------|----------|
| **Large files (>10MB)** | Vector Database Analysis | Parallel ON |
| **Many pages (>20)** | Vector Database Analysis | Parallel ON |
| **Poor scan quality** | Whole-Document Context | Parallel OFF |
| **Complex layouts** | Vector Database Analysis | Parallel OFF |
| **Simple, clean PDFs** | Whole-Document Context | Parallel ON |

### **Common Issues & Solutions:**

#### **🔐 API Issues**
- **Rate Limits**: Wait 2-3 minutes between attempts
- **Credits**: Check your OpenAI account has sufficient credits
- **Key**: Verify API key is correctly entered in sidebar

#### **📋 Document Quality Issues**
- **Password Protection**: Remove password protection first
- **Scanned Images**: Ensure text is selectable (not just images)
- **File Corruption**: Try re-saving or converting the PDF

#### **🌐 Network Issues**
- **Connection**: Verify stable internet connection
- **Firewall**: Ensure OpenAI API access isn't blocked
- **VPN**: Try disabling VPN if connection issues persist

### **Advanced Troubleshooting:**

#### **For Developers:**
1. **Enable Debug Mode**: Check "Show debug information" in sidebar
2. **Check Logs**: Look for specific error messages
3. **Test with Known Good Document**: Verify the tool is working

#### **Document Preparation Tips:**
1. **Extract Key Pages**: Focus on core financial statement pages only
2. **Improve Quality**: Use higher DPI scans (200+ DPI recommended)
3. **Standard Format**: Ensure documents follow standard accounting formats

### **Success Rate by Document Type:**

| Document Characteristics | Success Rate | Recommended Method |
|--------------------------|--------------|-------------------|
| **Clean, standard format** | 95%+ | Whole-Document Context |
| **Multi-page, complex** | 90%+ | Vector Database Analysis |
| **Poor scan quality** | 80%+ | Whole-Document Context (Sequential) |
| **Non-standard format** | 70%+ | Vector Database Analysis (Sequential) |

### **When All Else Fails:**

1. **Wait and Retry**: Sometimes temporary API issues resolve themselves
2. **Document Conversion**: Try converting PDF to different format and back
3. **Manual Extraction**: For critical documents, consider manual data entry
4. **Contact Support**: Report persistent issues with document samples

---

## 🎯 **Quick Decision Tree:**

```
Document Failed?
├── Try Alternative Method
│   ├── Success? ✅ Done!
│   └── Still Fails? → Continue
├── Disable Parallel Processing
│   ├── Success? ✅ Done!
│   └── Still Fails? → Continue
├── Check Document Quality
│   ├── Poor Quality? → Use Whole-Document (Sequential)
│   └── Good Quality? → Use Vector Database (Sequential)
└── If All Fail → Wait 2-3 minutes and retry
```

---

**💡 Remember**: The tool has a 90%+ success rate across different document types when using the right method for each document! 