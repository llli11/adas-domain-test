-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 10.82.77.87    Database: mydb_local
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `menu`
--

DROP TABLE IF EXISTS `menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `menu` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `name` varchar(20) NOT NULL COMMENT '菜单名称',
  `remark` json DEFAULT NULL COMMENT '保留字段',
  `menu_type` varchar(7) DEFAULT NULL COMMENT '菜单类型',
  `icon` varchar(100) DEFAULT NULL COMMENT '菜单图标',
  `path` varchar(100) NOT NULL COMMENT '菜单路径',
  `order` int NOT NULL DEFAULT '0' COMMENT '排序',
  `parent_id` int NOT NULL DEFAULT '0' COMMENT '父菜单ID',
  `is_hidden` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否隐藏',
  `component` varchar(100) NOT NULL COMMENT '组件',
  `keepalive` tinyint(1) NOT NULL DEFAULT '1' COMMENT '存活',
  `redirect` varchar(100) DEFAULT NULL COMMENT '重定向',
  PRIMARY KEY (`id`),
  KEY `idx_menu_created_b6922b` (`created_at`),
  KEY `idx_menu_updated_e6b0a1` (`updated_at`),
  KEY `idx_menu_name_b9b853` (`name`),
  KEY `idx_menu_path_bf95b2` (`path`),
  KEY `idx_menu_order_606068` (`order`),
  KEY `idx_menu_parent__bebd15` (`parent_id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `menu`
--

LOCK TABLES `menu` WRITE;
/*!40000 ALTER TABLE `menu` DISABLE KEYS */;
INSERT INTO `menu` VALUES (1,'2026-06-29 18:14:11.949869','2026-06-29 18:14:11.949903','系统管理',NULL,'catalog','carbon:gui-management','/system',1,0,0,'Layout',0,'/system/user'),(2,'2026-06-29 18:14:11.956627','2026-06-29 18:14:11.956664','用户管理',NULL,'menu','material-symbols:person-outline-rounded','user',1,1,0,'/system/user',0,NULL),(3,'2026-06-29 18:14:11.956719','2026-06-29 18:14:11.956736','角色管理',NULL,'menu','carbon:user-role','role',2,1,0,'/system/role',0,NULL),(4,'2026-06-29 18:14:11.956771','2026-06-29 18:14:11.956783','菜单管理',NULL,'menu','material-symbols:list-alt-outline','menu',3,1,0,'/system/menu',0,NULL),(5,'2026-06-29 18:14:11.956814','2026-06-29 18:14:11.956826','API管理',NULL,'menu','ant-design:api-outlined','api',4,1,0,'/system/api',0,NULL),(6,'2026-06-29 18:14:11.956857','2026-06-29 18:14:11.956869','部门管理',NULL,'menu','mingcute:department-line','dept',5,1,0,'/system/dept',0,NULL),(7,'2026-06-29 18:14:11.956898','2026-06-29 18:14:11.956909','审计日志',NULL,'menu','ph:clipboard-text-bold','auditlog',6,1,0,'/system/auditlog',0,NULL),(8,'2026-06-29 18:14:11.964888','2026-06-29 18:14:11.964913','测试路线管理',NULL,'catalog','material-symbols:route','/testroute',5,0,0,'Layout',0,'/testroute/mapway'),(9,'2026-06-29 18:14:11.972753','2026-07-21 19:29:39.842646','测试路线',NULL,'menu','material-symbols:map','mapway',0,8,0,'/testroute/mapway',1,NULL),(10,'2026-06-29 18:14:11.972813','2026-06-29 18:14:11.972825','合作项目城市详情',NULL,'menu','','city/:city',1,8,1,'/testroute/mapway/cityDetail',1,NULL),(11,'2026-06-29 18:14:11.972855','2026-07-21 19:29:32.028054','自研项目',NULL,'menu','material-symbols:science','selfdeveloped',2,8,1,'/testroute/selfdeveloped',1,NULL),(12,'2026-06-29 18:14:11.972896','2026-06-29 18:14:11.972908','自研城市详情',NULL,'menu','','selfdeveloped/city/:city',3,8,1,'/testroute/selfdeveloped/cityDetail',1,NULL),(14,'2026-06-29 18:14:11.987453','2026-06-29 18:14:11.987473','整车ECU版本管理',NULL,'menu','mdi-alert-box-outline','/ecu',10,0,0,'/ecu',0,''),(15,'2026-06-29 18:14:11.993479','2026-06-29 18:14:11.993497','车辆列表',NULL,'menu','car','',0,14,0,'/ecu',1,NULL),(16,'2026-06-29 18:14:11.993533','2026-06-29 18:14:11.993546','ECU详情',NULL,'menu','car','detail/:vin',1,14,1,'/ecu/detail',1,NULL),(17,'2026-06-29 18:14:11.993575','2026-06-29 18:14:11.993586','基线列表',NULL,'menu','list','target',2,14,0,'/ecu/target',1,NULL),(18,'2026-06-29 18:14:11.993615','2026-06-29 18:14:11.993626','目标详情',NULL,'menu','detail','target/detail/:target_name',3,14,1,'/ecu/target/detail',1,NULL),(19,'2026-06-29 18:14:11.993673','2026-06-29 18:14:11.993685','操作记录',NULL,'menu','history','logs',4,14,0,'/ecu/logs',1,NULL),(20,'2026-06-29 18:14:12.001018','2026-07-30 08:48:42.730889','车辆管理',NULL,'catalog','mdi:car-multiple','/vehicle',3,0,0,'Layout',0,'/vehicle/task-status'),(21,'2026-06-29 18:14:12.007495','2026-06-29 18:14:12.007513','外委管理',NULL,'catalog','material-symbols:engineering-outline','/contractor',4,0,0,'Layout',0,'/contractor/staff'),(22,'2026-06-29 18:14:12.013031','2026-06-29 18:14:12.013050','人员台账',NULL,'menu','material-symbols:person-outline-rounded','staff',1,21,0,'/contractor/staff',0,NULL),(28,'2026-06-29 18:14:12.013291','2026-06-29 18:14:12.013302','考评管理',NULL,'menu','material-symbols:star-outline','evaluation',7,21,0,'/contractor/evaluation',0,NULL),(29,'2026-06-29 20:08:51.109531','2026-08-12 11:16:15.238556','工具管理',NULL,'catalog','mdi:tools','/tool-management',6,0,0,'Layout',0,'/tool-management/tool-ledger'),(30,'2026-06-29 20:09:18.267263','2026-06-29 20:13:52.085114','设备台账',NULL,'menu','mdi:clipboard-list-outline','tool-ledger',1,29,0,'/tool-management/tool-ledger',0,''),(31,'2026-06-29 20:14:18.256078','2026-06-29 20:14:18.256098','借用记录',NULL,'menu','mdi:swap-horizontal','tool-borrow',2,29,0,'/tool-management/tool-borrow',0,''),(32,'2026-06-29 20:15:42.083701','2026-06-29 20:15:49.640751','盘点管理',NULL,'menu','mdi:clipboard-check-outline','tool-inventory',3,29,0,'/tool-management/tool-inventory',0,''),(33,'2026-06-29 20:16:12.168341','2026-06-29 20:16:12.168359','需求管理',NULL,'menu','mdi:shopping-outline','tool-requirement',4,29,0,'/tool-management/tool-requirement',0,''),(34,'2026-06-29 20:17:20.001301','2026-08-12 11:16:15.265332','费用管理',NULL,'catalog','mdi:cash-multiple','/expense-management',7,0,0,'Layout',0,'/expense-management/dashboard'),(35,'2026-06-29 20:17:51.107447','2026-06-29 20:17:51.107465','费用概览',NULL,'menu','mdi:chart-bar','dashboard',1,34,0,'/expense-management/dashboard',0,''),(36,'2026-06-29 20:18:18.165123','2026-06-29 20:18:18.165142','每日记录',NULL,'menu','mdi:clipboard-text-outline','daily-record',2,34,0,'/expense-management/daily-record',0,''),(37,'2026-06-29 20:18:47.642627','2026-06-29 20:18:47.642650','月度结算',NULL,'menu','mdi:calendar-check-outline','monthly-settlement',3,34,0,'/expense-management/monthly-settlement',0,''),(38,'2026-06-29 20:19:12.250577','2026-06-29 20:19:12.250605','预算预警',NULL,'menu','mdi:alert-circle-outline','budget-alert',4,34,0,'/expense-management/budget-alert',0,''),(39,'2026-07-21 18:29:23.413829','2026-07-21 18:29:23.413863','版本管理',NULL,'menu','ph:user-list-bold','/versionIndex',13,0,0,'/versionIndex',0,''),(40,'2026-07-30 08:48:42.736813','2026-07-30 08:48:42.736847','车辆任务状态',NULL,'menu','material-symbols:task-alt','task-status',1,20,0,'/vehicle/task-status',1,NULL),(41,'2026-07-30 08:48:42.742131','2026-07-30 08:48:42.742164','车辆数据详情',NULL,'menu','material-symbols:table-rows','data-detail',2,20,0,'/vehicle/data-detail',1,NULL),(42,'2026-07-30 08:48:42.751241','2026-07-30 08:48:42.751283','异常状态提醒',NULL,'menu','material-symbols:notifications-active','expiry-alerts',3,20,0,'/vehicle/expiry-alerts',1,NULL),(43,'2026-07-30 08:48:42.755633','2026-07-30 08:48:42.755662','数据源管理',NULL,'menu','material-symbols:cloud-sync','data-source',4,20,0,'/vehicle/data-source',1,NULL),(44,'2026-08-07 16:49:04.719785','2026-08-07 16:49:04.719824','人员考核管理',NULL,'menu','material-symbols:assignment-turned-in-outline','assessment',2,21,0,'/contractor/assessment',0,NULL);
/*!40000 ALTER TABLE `menu` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:40
