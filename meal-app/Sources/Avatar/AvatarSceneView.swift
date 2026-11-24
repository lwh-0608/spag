import SwiftUI
import SceneKit

/// 3D 小人参数：体重/身高决定身材，其余为“捏脸”选项
struct AvatarParameters: Equatable {
    var weightKg: Double = 70
    var heightCm: Double = 175
    var skinHex: String = "F2C9A0"
    var hairStyle: String = "short"
    var hairHex: String = "1C1C1E"
    var eyeHex: String = "5B3A29"
    var faceWidth: Double = 1.0
}

extension UIColor {
    convenience init(hexString: String) {
        var hex = hexString.trimmingCharacters(in: .whitespacesAndNewlines)
        if hex.hasPrefix("#") { hex.removeFirst() }
        var value: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&value)
        let r = CGFloat((value >> 16) & 0xFF) / 255
        let g = CGFloat((value >> 8) & 0xFF) / 255
        let b = CGFloat(value & 0xFF) / 255
        self.init(red: r, green: g, blue: b, alpha: 1)
    }
}

struct AvatarSceneView: UIViewRepresentable {
    var parameters: AvatarParameters

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> SCNView {
        let view = SCNView()
        view.scene = context.coordinator.scene
        view.backgroundColor = .clear
        view.isOpaque = false
        view.antialiasingMode = .multisampling4X
        view.allowsCameraControl = true
        view.autoenablesDefaultLighting = false
        context.coordinator.apply(parameters, animated: false)
        return view
    }

    func updateUIView(_ uiView: SCNView, context: Context) {
        context.coordinator.apply(parameters, animated: true)
    }

    final class Coordinator {
        let scene = SCNScene()
        private let root = SCNNode()

        private let skinMaterial = SCNMaterial()
        private let hairMaterial = SCNMaterial()
        private let irisMaterial = SCNMaterial()
        private let whiteMaterial = SCNMaterial()
        private let darkMaterial = SCNMaterial()

        private var body: SCNNode!
        private var belly: SCNNode!
        private var head: SCNNode!
        private var ears: [SCNNode] = []
        private var eyeNodes: [SCNNode] = []
        private var browNodes: [SCNNode] = []
        private var hairCap: SCNNode!
        private var hairBack: SCNNode!
        private var hairBun: SCNNode!
        private var legs: [SCNNode] = []
        private var arms: [SCNNode] = []

        private let headBase = SCNVector3(0.225, 0.215, 0.205)

        init() {
            build()
        }

        private func makeMaterial(_ color: UIColor, roughness: CGFloat = 0.75) -> SCNMaterial {
            let m = SCNMaterial()
            m.diffuse.contents = color
            m.roughness.contents = roughness
            m.lightingModel = .physicallyBased
            return m
        }

        private func sphere(radius: CGFloat, material: SCNMaterial) -> SCNNode {
            let node = SCNNode(geometry: SCNSphere(radius: radius))
            node.geometry?.firstMaterial = material
            return node
        }

        private func capsule(radius: CGFloat, height: CGFloat, material: SCNMaterial) -> SCNNode {
            let node = SCNNode(geometry: SCNCapsule(capRadius: radius, height: height))
            node.geometry?.firstMaterial = material
            return node
        }

        private func build() {
            skinMaterial.diffuse.contents = UIColor(hexString: "F2C9A0")
            skinMaterial.roughness.contents = 0.8
            skinMaterial.lightingModel = .physicallyBased
            hairMaterial.diffuse.contents = UIColor(hexString: "1C1C1E")
            hairMaterial.roughness.contents = 0.9
            hairMaterial.lightingModel = .physicallyBased
            irisMaterial.diffuse.contents = UIColor(hexString: "5B3A29")
            irisMaterial.roughness.contents = 0.35
            irisMaterial.lightingModel = .physicallyBased
            whiteMaterial.diffuse.contents = UIColor(white: 0.98, alpha: 1)
            whiteMaterial.roughness.contents = 0.25
            whiteMaterial.lightingModel = .physicallyBased
            darkMaterial.diffuse.contents = UIColor(white: 0.06, alpha: 1)
            darkMaterial.roughness.contents = 0.4
            darkMaterial.lightingModel = .physicallyBased

            scene.rootNode.addChildNode(root)

            // 灯光
            let ambient = SCNLight()
            ambient.type = .ambient
            ambient.color = UIColor(white: 0.74, alpha: 1)
            ambient.intensity = 440
            let ambientNode = SCNNode()
            ambientNode.light = ambient
            scene.rootNode.addChildNode(ambientNode)

            let key = SCNLight()
            key.type = .directional
            key.color = UIColor(white: 1, alpha: 1)
            key.intensity = 950
            key.castsShadow = true
            key.shadowMode = .deferred
            key.shadowSampleCount = 8
            let keyNode = SCNNode()
            keyNode.light = key
            keyNode.position = SCNVector3(2.0, 3.2, 2.6)
            keyNode.look(at: SCNVector3(0, 1.0, 0))
            scene.rootNode.addChildNode(keyNode)

            let rim = SCNLight()
            rim.type = .omni
            rim.color = UIColor(red: 0.62, green: 0.74, blue: 1.0, alpha: 1)
            rim.intensity = 300
            let rimNode = SCNNode()
            rimNode.light = rim
            rimNode.position = SCNVector3(-1.7, 2.3, -1.6)
            scene.rootNode.addChildNode(rimNode)

            // 相机
            let camera = SCNCamera()
            camera.fieldOfView = 32
            camera.zNear = 0.1
            camera.zFar = 30
            camera.wantsHDR = true
            let cameraNode = SCNNode()
            cameraNode.camera = camera
            cameraNode.position = SCNVector3(0, 0.95, 3.1)
            cameraNode.look(at: SCNVector3(0, 0.88, 0))
            scene.rootNode.addChildNode(cameraNode)

            // 脚
            for side in [-1.0, 1.0] {
                let foot = sphere(radius: 0.105, material: makeMaterial(UIColor(white: 0.93, alpha: 1), roughness: 0.5))
                foot.scale = SCNVector3(0.62, 0.30, 1.0)
                foot.position = SCNVector3(0.10 * side, 0.05, 0.04)
                root.addChildNode(foot)
            }

            // 腿
            for side in [-1.0, 1.0] {
                let leg = capsule(radius: 0.070, height: 0.52, material: skinMaterial)
                leg.position = SCNVector3(0.10 * side, 0.34, 0)
                root.addChildNode(leg)
                legs.append(leg)
            }

            // 身体（胶囊：肩到胯圆润一体）
            body = capsule(radius: 0.19, height: 0.72, material: skinMaterial)
            body.position = SCNVector3(0, 0.94, 0)
            root.addChildNode(body)

            // 肚子（体重偏大时显示）
            belly = sphere(radius: 1, material: skinMaterial)
            belly.scale = SCNVector3(0.16, 0.13, 0.13)
            belly.position = SCNVector3(0, 0.88, 0.10)
            belly.isHidden = true
            root.addChildNode(belly)

            // 脖子（很短，藏在头和身体之间）
            let neck = capsule(radius: 0.09, height: 0.08, material: skinMaterial)
            neck.position = SCNVector3(0, 1.30, 0)
            root.addChildNode(neck)

            // 头
            head = sphere(radius: 1, material: skinMaterial)
            head.scale = headBase
            head.position = SCNVector3(0, 1.52, 0)
            root.addChildNode(head)

            // 耳朵
            for side in [-1.0, 1.0] {
                let ear = sphere(radius: 0.032, material: skinMaterial)
                ear.scale = SCNVector3(0.5, 1.0, 1.0)
                ear.position = SCNVector3(0.205 * side, 1.52, 0)
                root.addChildNode(ear)
                ears.append(ear)
            }

            // 眼睛（眼白 + 虹膜 + 瞳孔）
            for side in [-1.0, 1.0] {
                let sclera = sphere(radius: 0.036, material: whiteMaterial)
                sclera.scale = SCNVector3(1, 1.15, 0.5)
                sclera.position = SCNVector3(0.078 * side, 1.535, 0.196)
                root.addChildNode(sclera)

                let iris = sphere(radius: 0.021, material: irisMaterial)
                iris.scale = SCNVector3(1, 1, 0.4)
                iris.position = SCNVector3(0.078 * side, 1.533, 0.212)
                root.addChildNode(iris)

                let pupil = sphere(radius: 0.010, material: darkMaterial)
                pupil.scale = SCNVector3(1, 1, 0.4)
                pupil.position = SCNVector3(0.078 * side, 1.533, 0.218)
                root.addChildNode(pupil)
                eyeNodes.append(sclera)
            }

            // 眉毛
            for side in [-1.0, 1.0] {
                let brow = SCNNode(geometry: SCNBox(width: 0.062, height: 0.012, length: 0.014, chamferRadius: 0.005))
                brow.geometry?.firstMaterial = darkMaterial
                brow.position = SCNVector3(0.078 * side, 1.605, 0.190)
                brow.eulerAngles.z = Float(0.08 * side)
                root.addChildNode(brow)
                browNodes.append(brow)
            }

            // 鼻子 + 嘴
            let nose = sphere(radius: 0.020, material: skinMaterial)
            nose.scale = SCNVector3(1, 0.85, 1.1)
            nose.position = SCNVector3(0, 1.495, 0.202)
            root.addChildNode(nose)

            let mouth = SCNNode(geometry: SCNBox(width: 0.070, height: 0.016, length: 0.014, chamferRadius: 0.007))
            mouth.geometry?.firstMaterial = makeMaterial(UIColor(red: 0.68, green: 0.34, blue: 0.33, alpha: 1), roughness: 0.5)
            mouth.position = SCNVector3(0, 1.435, 0.196)
            root.addChildNode(mouth)

            // 头发
            hairCap = sphere(radius: 1, material: hairMaterial)
            hairCap.scale = SCNVector3(0.235, 0.13, 0.20)
            hairCap.position = SCNVector3(0, 1.62, 0)
            root.addChildNode(hairCap)

            hairBack = sphere(radius: 1, material: hairMaterial)
            hairBack.scale = SCNVector3(0.215, 0.28, 0.10)
            hairBack.position = SCNVector3(0, 1.38, -0.12)
            root.addChildNode(hairBack)

            hairBun = sphere(radius: 0.075, material: hairMaterial)
            hairBun.position = SCNVector3(0, 1.73, -0.03)
            root.addChildNode(hairBun)

            // 手臂（手掌为子节点，跟随旋转）
            for side in [-1.0, 1.0] {
                let arm = capsule(radius: 0.052, height: 0.44, material: skinMaterial)
                arm.position = SCNVector3(0.245 * side, 1.02, 0)
                arm.eulerAngles.z = Float(0.10 * side)
                root.addChildNode(arm)
                arms.append(arm)

                let hand = sphere(radius: 0.060, material: skinMaterial)
                hand.scale = SCNVector3(1, 0.9, 0.8)
                hand.position = SCNVector3(0, -0.22, 0)
                arm.addChildNode(hand)
            }
        }

        func apply(_ p: AvatarParameters, animated: Bool) {
            let heightM = max(120, p.heightCm) / 100.0
            let bmi = max(12, p.weightKg / (heightM * heightM))
            let extra = max(0, bmi - 22)
            let thin = max(0, 22 - bmi)
            let heightScale = min(1.12, max(0.90, heightM / 1.75))

            let bodyWidth = min(0.34, max(0.16, 0.195 + extra * 0.024 - thin * 0.010))
            let bodyDepth = min(0.30, max(0.14, 0.195 + extra * 0.020 - thin * 0.008))
            let limbScale = min(1.45, max(0.82, 1.0 + extra * 0.020 - thin * 0.012))
            let bellyVisible = extra > 1.2

            let updates: () -> Void = {
                self.body.scale = SCNVector3(bodyWidth / 0.195, 1.0, bodyDepth / 0.195)
                self.belly.scale = SCNVector3(min(0.32, 0.16 + extra * 0.022), 0.12, 0.10 + extra * 0.012)
                self.belly.position = SCNVector3(0, 0.86, bodyDepth * 0.62)
                self.belly.isHidden = !bellyVisible

                self.head.scale = SCNVector3(self.headBase.x * Float(p.faceWidth),
                                             self.headBase.y,
                                             self.headBase.z)
                for ear in self.ears {
                    ear.position.x = 0.205 * Float(p.faceWidth) * (ear.position.x > 0 ? 1 : -1)
                }
                for eye in self.eyeNodes {
                    eye.position.x = 0.078 * Float(p.faceWidth) * (eye.position.x > 0 ? 1 : -1)
                }
                for brow in self.browNodes {
                    brow.position.x = 0.078 * Float(p.faceWidth) * (brow.position.x > 0 ? 1 : -1)
                }

                for leg in self.legs {
                    leg.scale = SCNVector3(limbScale, 1, limbScale)
                }
                for arm in self.arms {
                    arm.position.x = Float((0.245 + extra * 0.016) * (arm.position.x > 0 ? 1 : -1))
                    arm.scale = SCNVector3(limbScale, 1, limbScale)
                }

                switch p.hairStyle {
                case "long":
                    self.hairBack.isHidden = false
                    self.hairBun.isHidden = true
                case "bun":
                    self.hairBack.isHidden = true
                    self.hairBun.isHidden = false
                case "buzz":
                    self.hairBack.isHidden = true
                    self.hairBun.isHidden = true
                    self.hairCap.scale = SCNVector3(0.230 * p.faceWidth, 0.065, 0.195)
                    self.hairCap.position = SCNVector3(0, 1.625, 0)
                default:
                    self.hairBack.isHidden = true
                    self.hairBun.isHidden = true
                    self.hairCap.scale = SCNVector3(0.235 * p.faceWidth, 0.13, 0.20)
                    self.hairCap.position = SCNVector3(0, 1.62, 0)
                }

                self.root.scale = SCNVector3(heightScale, heightScale, heightScale)

                self.skinMaterial.diffuse.contents = UIColor(hexString: p.skinHex)
                self.hairMaterial.diffuse.contents = UIColor(hexString: p.hairHex)
                self.irisMaterial.diffuse.contents = UIColor(hexString: p.eyeHex)
            }

            if animated {
                SCNTransaction.begin()
                SCNTransaction.animationDuration = 0.28
                SCNTransaction.animationTimingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
                updates()
                SCNTransaction.commit()
            } else {
                updates()
            }
        }
    }
}
