import cv2
import json
import os
import collections

# res = json.load(open("annotations.json"))
images_path = "./QYS_rear_left_20190323_sihuan_1000"

anno_dir = os.listdir('./annotations')

merge_anno = []
for i in range(len(anno_dir)):
    merge_anno.extend(json.load(open(os.path.join('./annotations', anno_dir[i]))))

res = merge_anno


# print(res[359])


# print(len(merge_anno)),997sample fr:invis r:vis

def oneIsBelongSameSample(vehicle, headlight):
    vehx1 = vehicle['x']
    vehy1 = vehicle['y']
    vehx2 = vehicle['x'] + vehicle['width']
    vehy2 = vehicle['y'] + vehicle['height']
    hlx1 = headlight['x']
    hly1 = headlight['y']
    hlx2 = headlight['x'] + headlight['width']
    hly2 = headlight['y'] + headlight['height']
    if hlx2 > 1920:  # fr zhedang
        hlx2 = 1920
    if vehx1 - 50 <= hlx1 <= vehx2 and vehx1 <= hlx2 <= vehx2 and vehy1 <= hly1 <= vehy2 and vehy1 <= hly2 <= vehy2:
        return True
    else:
        return False


def twoIsBelongSameSample(vehicle_list, matchidx, classInfo):
    vehi_1 = vehicle_list[matchidx[0]]
    vehi_2 = vehicle_list[matchidx[1]]
    if vehi_1['headlight(h)'] is not None and vehi_2['headlight(h)'] is None:
        return matchidx[1]
    elif vehi_2['headlight(h)'] is not None and vehi_1['headlight(h)'] is None:
        return matchidx[0]
    elif vehi_1['headlight(h)'] is None and vehi_2['headlight(h)'] is None:
        d1 = classInfo['x'] - vehi_1['x'] + vehi_1['y'] + vehi_1['height'] - classInfo['y']
        d2 = classInfo['x'] - vehi_2['x'] + vehi_2['y'] + vehi_2['height'] - classInfo['y']
        if d1 <= d2:
            return matchidx[0]
        else:
            return matchidx[1]
    else:
        return -1


def process_annp():
    totalAnnoList = []
    for i in range(len(res)):
        imgAnno = res[i]
        imgName = imgAnno['filename'].split('//')[-1]
        img = cv2.imread(os.path.join(images_path, imgName))
        classAnno = imgAnno['annotations']
        numClass = len(classAnno)
        newImgAnno = {}
        newClassList = []
        id = 0
        # adjust classAnno,vehicle headlight order
        newClassAnno = []
        # total Anno list
        for tempClass in classAnno:
            if tempClass['class'] == 'vehicle(v)':
                newClassAnno.insert(0, tempClass)
            else:
                newClassAnno.append(tempClass)
        classAnno = newClassAnno
        for j in range(numClass):
            classInfo = classAnno[j]
            x = classInfo['x']
            y = classInfo['y']
            w = classInfo['width']
            h = classInfo['height']
            classType = classInfo['class']
            if classType == "vehicle(v)":
                classSubType = classInfo['veh']
                direction = classSubType.split("_")[-1]
                if direction != 's':
                    continue
                else:
                    # add vehicle id
                    classInfo['id'] = 0
                    # add headlight state -1:None,0:invisible 1:visible
                    classInfo['headlightVisible'] = -1
                    # add headlight info: None or {...}
                    classInfo['headlight(h)'] = None
                    classInfo['id'] = id
                    id += 1
            elif classType == 'headlight(h)' and classInfo['hl'] == 'headlight_r':
                # belong to ? vehicle
                matchVehIdx = []
                for vhInfoIdx, vhInfo in enumerate(newClassList):
                    if oneIsBelongSameSample(vhInfo, classInfo):
                        matchVehIdx.append(vhInfoIdx)
                print("r:", matchVehIdx)
                assert len(matchVehIdx) == 1 or len(matchVehIdx) == 2 or len(matchVehIdx) == 0 or len(matchVehIdx) == 3
                if len(matchVehIdx) == 1:  # one match
                    if newClassList[matchVehIdx[0]]['headlight(h)'] is None:
                        newClassList[matchVehIdx[0]]['headlightVisible'] = 1
                        newClassList[matchVehIdx[0]]['headlight(h)'] = classInfo
                    else:
                        continue
                elif len(matchVehIdx) == 0:
                    continue
                elif len(matchVehIdx) == 2:
                    # go on match
                    idx = twoIsBelongSameSample(newClassList, matchVehIdx, classInfo)
                    if idx != -1:
                        newClassList[idx]['headlight(h)'] = classInfo
                    else:
                        continue
                elif len(matchVehIdx) == 3:
                    idx1 = twoIsBelongSameSample(newClassList, [matchVehIdx[0], matchVehIdx[1]], classInfo)
                    idx2 = twoIsBelongSameSample(newClassList, [matchVehIdx[1], matchVehIdx[2]], classInfo)
                    idx3 = twoIsBelongSameSample(newClassList, [matchVehIdx[0], matchVehIdx[2]], classInfo)
                    num = [idx1, idx2, idx3]
                    matchNum = list(collections.Counter(num).keys())[0]
                    newClassList[matchNum]['headlight(h)'] = classInfo

            elif classType == "headlight(h)" and classInfo['hl'] == 'headlight_fr':
                # belong to ? vehicle
                matchVehIdx = []
                for vhInfoIdx, vhInfo in enumerate(newClassList):
                    if oneIsBelongSameSample(vhInfo, classInfo):
                        matchVehIdx.append(vhInfoIdx)
                print("fr:", matchVehIdx)
                assert len(matchVehIdx) == 1 or len(matchVehIdx) == 2 or len(matchVehIdx) == 0 or len(matchVehIdx) == 3
                if len(matchVehIdx) == 1:  # one match
                    if newClassList[matchVehIdx[0]]['headlight(h)'] is None:
                        newClassList[matchVehIdx[0]]['headlightVisible'] = 0
                        newClassList[matchVehIdx[0]]['headlight(h)'] = classInfo
                    else:
                        continue
                elif len(matchVehIdx) == 2:
                    # go on match
                    idx = twoIsBelongSameSample(newClassList, matchVehIdx, classInfo)
                    if idx != -1:
                        newClassList[idx]['headlight(h)'] = classInfo
                    else:
                        continue
                elif len(matchVehIdx) == 3:
                    idx1 = twoIsBelongSameSample(newClassList, [matchVehIdx[0], matchVehIdx[1]], classInfo)
                    idx2 = twoIsBelongSameSample(newClassList, [matchVehIdx[1], matchVehIdx[2]], classInfo)
                    idx3 = twoIsBelongSameSample(newClassList, [matchVehIdx[0], matchVehIdx[2]], classInfo)
                    num = [idx1, idx2, idx3]
                    matchNum = list(collections.Counter(num).keys())[0]
                    newClassList[matchNum]['headlight(h)'] = classInfo
                elif len(matchVehIdx) == 0:
                    continue
            else:
                continue
            if classType == 'vehicle(v)':
                newClassList.append(classInfo)
        newImgAnno['annotations'] = newClassList
        newImgAnno['class'] = imgAnno['class']
        newImgAnno['filename'] = imgAnno['filename']
        totalAnnoList.append(newImgAnno)
        print("done:", i)
    return totalAnnoList


totalAnnoList = process_annp()
import random

random.shuffle(totalAnnoList)
train_list = totalAnnoList[0:800]
test_list = totalAnnoList[800::]
print("train:", len(train_list))
print("test:", len(test_list))
with open("train.json", "w") as f:
    f.write(json.dumps(train_list, indent=4))
with open("test.json", "w") as f:
    f.write(json.dumps(test_list, indent=4))


# vis anno
def vis_new_anno(path="new_annotations.json"):
    res = json.load(open(path))
    for i in range(0, len(res)):
        imgAnno = res[i]
        imgName = imgAnno['filename'].split('\\')[-1]
        img = cv2.imread(os.path.join(images_path, imgName))
        classAnno = imgAnno['annotations']
        for j in range(len(classAnno)):
            classInfo = classAnno[j]
            x = classInfo['x']
            y = classInfo['y']
            w = classInfo['width']
            h = classInfo['height']
            if classInfo['headlightVisible'] == -1:
                cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255), 3)
                center_x = int(x)
                center_y = int(y + 5)
                cv2.putText(img, str(j), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            else:
                headlight = classInfo['headlight(h)']
                # draw vehicle
                hx = headlight['x']
                hy = headlight['y']
                hw = headlight['width']
                hh = headlight['height']
                cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255), 3)
                plot_x = int(x)
                plot_y = int(y + 5)
                cv2.putText(img, str(j), (plot_x, plot_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                # draw headlight
                cv2.rectangle(img, (int(hx), int(hy)), (int(hx + hw), int(hy + hh)), (0, 0, 255), 3)
                plot_hx = int(hx)
                plot_hy = int(hy + 5)
                cv2.putText(img, str(j), (plot_hx, plot_hy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("img:" + str(i), img)
        if i == 20:
            break
    cv2.waitKey()


vis_new_anno()
